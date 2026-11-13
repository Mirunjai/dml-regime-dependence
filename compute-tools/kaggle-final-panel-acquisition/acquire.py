"""Acquire a separately registered contemporaneous panel; no SCM or donor search."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,platform,subprocess,sys,time,zipfile
if importlib.util.find_spec('yfinance') is None:
    subprocess.run([sys.executable,'-m','pip','install','yfinance'],check=True)
import yfinance as yf
import pandas as pd
import numpy as np
OUT=Path('/kaggle/working/panel');OUT.mkdir(exist_ok=False)
requests=[(s,'2007-01-01','2022-01-01','registered_panel' if s not in ('SPY','^GSPC') else 'market') for s in ['CRM','FAST','MHK','SWKS','ETSY','TER','SPY','^GSPC']]
requests += [('^VIX','2000-01-01','2022-01-01','regime_source'),('BFH','2012-12-01','2014-04-01','historical_identity_probe_only_not_in_panel')]
logs=[]
for symbol,start,end,role in requests:
    started=time.perf_counter();record={'symbol':symbol,'start_inclusive':start,'end_exclusive':end,'role':role,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auto_adjust':False,'actions':True,'repair':False,'keepna':True,'provider':'Yahoo Finance via official yfinance API','package_version':yf.__version__}
    try:
        frame=yf.download(symbol,start=start,end=end,interval='1d',auto_adjust=False,actions=True,repair=False,keepna=True,progress=False,threads=False,timeout=45,multi_level_index=False)
        if frame is None or frame.empty:raise ValueError('Provider returned no rows')
        if frame.index.has_duplicates:raise ValueError('Duplicate provider dates')
        frame.index.name='date'
        frame.index=pd.to_datetime(frame.index).tz_localize(None).normalize()
        frame=frame.sort_index()
        file=OUT/(symbol.replace('^','INDEX_')+'.csv')
        frame.to_csv(file,float_format='%.17g')
        record.update(status='ok',rows=len(frame),first=str(frame.index.min().date()),last=str(frame.index.max().date()),columns=list(frame.columns),file=file.name,sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    except Exception as exc:record.update(status='failed',error=repr(exc),rows=0)
    record['seconds']=time.perf_counter()-started;logs.append(record);print(json.dumps(record),flush=True)
    time.sleep(.7)
manifest={'schema':'contemporaneous_panel_acquisition_v1','purpose':'Same fixed six firms, common 2016-2021 window; original event roster preserved','requests':logs,'python':platform.python_version(),'packages':{'yfinance':yf.__version__,'pandas':pd.__version__,'numpy':np.__version__},'raw_provider_data_not_for_redistribution':True,'historical_authentication':'Fresh acquisition is not the missing original input file. BFH is an identity probe only; no unverified ticker substitution.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
with zipfile.ZipFile('/kaggle/working/panel_acquisition.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in OUT.iterdir():z.write(f,f.name)
print('Acquisition complete:',sum(r['status']=='ok' for r in logs),'of',len(logs))
