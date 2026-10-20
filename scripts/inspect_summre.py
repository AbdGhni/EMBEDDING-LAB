# EL-003 : inventaire texte seul de SUMM-RE (lecture par colonnes, sans audio). Usage : python -I scripts/inspect_summre.py
import pyarrow.parquet as pq, collections, json
from huggingface_hub import HfFileSystem
fs=HfFileSystem(); R="datasets/linagora/SUMM-RE@47cb4ec3437ef5497b6092b8c6d1e0b5b1d86dc0/data"
out={}
for split in ["dev","test","train"]:
    ids=[]; nchar=0
    for p in sorted(fs.glob(f"{R}/{split}/*.parquet")):
        with fs.open(p,"rb",block_size=1<<20) as f:
            t=pq.ParquetFile(f).read(columns=["meeting_id","speaker_id","transcript"])
        ids+=list(zip(t["meeting_id"].to_pylist(),t["speaker_id"].to_pylist()))
        nchar+=sum(len(x or "") for x in t["transcript"].to_pylist())
    m=sorted(set(i for i,_ in ids)); g=sorted(set(i.split("_")[0][:-1] for i in m))
    out[split]=dict(tracks=len(ids),meetings=len(m),groups=g,chars=nchar,sample=m[:6])
    print(split,len(ids),"tracks",len(m),"meetings",len(g),"groups",nchar,"chars",m[:6])
gs={k:set(v["groups"]) for k,v in out.items()}
print("overlap dev/test",gs["dev"]&gs["test"],"train/test",gs["train"]&gs["test"],"train/dev",gs["train"]&gs["dev"])

