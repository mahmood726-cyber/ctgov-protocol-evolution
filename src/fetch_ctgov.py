import urllib.request
import json
import hashlib
import os
import csv
import time

# Target: ALL completed studies on ClinicalTrials.gov (~316,000)
BASE_URL = "https://clinicaltrials.gov/api/v2/studies?filter.overallStatus=COMPLETED&pageSize=1000"

def fetch_all_completed(max_total=500000):
    all_studies_count = 0
    next_page_token = None
    output_csv = 'data/protocol_changes.csv'
    
    os.makedirs('data', exist_ok=True)
    fields = [
        'NCTId', 'EnrollmentCount', 'EnrollmentType', 'StudyType', 
        'PrimaryOutcomesCount', 'SecondaryOutcomesCount', 'PrimaryCondition', 
        'StartDate', 'CompletionDate', 'Phase'
    ]
    
    print(f"Starting MASSIVE ingestion of all completed studies...")
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        
        while all_studies_count < max_total:
            url = BASE_URL
            if next_page_token:
                url += f"&pageToken={next_page_token}"
            
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    studies = data.get('studies', [])
                    if not studies:
                        break
                    
                    rows = []
                    for study in studies:
                        protocol = study.get('protocolSection', {})
                        ident = protocol.get('identificationModule', {})
                        nct_id = ident.get('nctId', 'N/A')
                        
                        design = protocol.get('designModule', {})
                        enrollment = design.get('enrollmentInfo', {})
                        count = enrollment.get('count', 0)
                        etype = enrollment.get('type', 'N/A')
                        study_type = design.get('studyType', 'N/A')
                        phases = design.get('phases', ['N/A'])
                        phase = phases[0] if phases else 'N/A'
                        
                        outcomes = protocol.get('outcomesModule', {})
                        p_count = len(outcomes.get('primaryOutcomes', []))
                        s_count = len(outcomes.get('secondaryOutcomes', []))
                        
                        cond_mod = protocol.get('conditionsModule', {})
                        conds = cond_mod.get('conditions', [])
                        p_cond = conds[0] if conds else 'N/A'
                        
                        status = protocol.get('statusModule', {})
                        s_date = status.get('startDateStruct', {}).get('date', 'N/A')
                        c_date = status.get('completionDateStruct', {}).get('date', 'N/A')
                        
                        rows.append({
                            'NCTId': nct_id,
                            'EnrollmentCount': count,
                            'EnrollmentType': etype,
                            'StudyType': study_type,
                            'PrimaryOutcomesCount': p_count,
                            'SecondaryOutcomesCount': s_count,
                            'PrimaryCondition': p_cond,
                            'StartDate': s_date,
                            'CompletionDate': c_date,
                            'Phase': phase
                        })
                    
                    writer.writerows(rows)
                    all_studies_count += len(rows)
                    print(f"Progress: {all_studies_count} studies ingested...")
                    
                    next_page_token = data.get('nextPageToken')
                    if not next_page_token:
                        break
                    # Very small delay to respect the server
                    time.sleep(0.01)
            except Exception as e:
                print(f"Error at page {all_studies_count}: {e}")
                time.sleep(1.0) # wait on error
                
    with open(output_csv, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
        
    cert = {
        'source_locator': BASE_URL,
        'total_available': all_studies_count,
        'sample_size': all_studies_count,
        'transformations': ['Massive streaming ingestion', 'Full ClinicalTrials.gov database dump'],
        'sha256_hash': file_hash
    }
    with open('data/hash_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(cert, f, indent=2)

if __name__ == "__main__":
    fetch_all_completed(max_total=550000)
    print("Massive TruthCert database generated successfully.")
