import http from 'k6/http';
import { check } from 'k6';

// Configuration via Environment Variables
const TARGET_RPM = parseInt(__ENV.TARGET_RPM) || 1000; // Default 1k RPM
const DURATION = __ENV.DURATION || '60s';
const BASE_URL = __ENV.BASE_URL || 'http://host.docker.internal:8000';
const ENDPOINT = __ENV.ENDPOINT || '/health'; // Change to trigger rate limits

// Configure execution
export const options = {
    scenarios: {
        constant_request_rate: {
            executor: 'constant-arrival-rate',
            rate: TARGET_RPM,
            timeUnit: '1m', // rate per minute
            duration: DURATION,
            preAllocatedVUs: 20,
            maxVUs: 200,
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
    },
};

export default function () {
    const url = `${BASE_URL}${ENDPOINT}`;

    const res = http.get(url);

    // Check based on expected behavior (200 OK or 429 Too Many Requests)
    check(res, {
        'status is expected': (r) => r.status === 200 || r.status === 429,
    });
}