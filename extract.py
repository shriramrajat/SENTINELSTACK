import json
import re

files = ['200.html', '500.html', '1000.html']
for fn in files:
    try:
        with open('public/' + fn, 'r', encoding='utf-8') as f:
            content = f.read()
            m = re.search(r'report_data\s*=\s*(\{.*?\})\s*</script>', content, re.DOTALL)
            if m:
                d = json.loads(m.group(1))
                aggr = None
                for r in d.get('requests', []):
                    if r.get('name') == 'Aggregated' or r.get('method') == '':
                        aggr = r
                        break
                if aggr:
                    print(f"{fn} summary -> RPS: {aggr.get('current_rps', 0):.1f}, Avg: {aggr.get('avg_response_time', 0):.1f}, p95: {aggr.get('ninty_fifth_response_time', 0):.1f}, p99: {aggr.get('ninty_ninth_response_time', 0):.1f}, Fails: {aggr.get('num_failures', 0)}")
                else:
                    print(f"{fn} -> requests list missing Aggregated")
            else:
                
                stats = re.search(r'\"requests\":\s*(\[.*?\])', content, re.DOTALL)
                if stats:
                    print(f'{fn} -> found JSON, length {len(stats.group(1))}')
                else:
                    print(f'{fn} -> stats not found entirely')
    except Exception as e:
        print(f'{fn} -> error: {e}')
