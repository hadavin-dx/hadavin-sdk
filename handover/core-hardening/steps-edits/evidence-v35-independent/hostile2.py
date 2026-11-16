import re
src=open('/home/user/hadavin-sdk/handover/core-hardening/steps-edits/evidence-v35-independent/hostile.py',encoding='utf-8').read()
head=src[:src.index("E = [")]
tail=src[src.index("tmp = tempfile.mkdtemp()"):]
mid='''E=[]
PAGEE=[('G01','OWNER-APPENDIX-v35-A.md','18:29 UTC = 23:59 IST','18:29 UTC = 23:49 IST','built appendix A: deadline pair changed'),
('G07','OWNER-CARD-v35-B.md','Paste once','Paste twice','built card B: typed word')]
'''
exec(head+mid+tail)
