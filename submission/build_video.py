"""Create an explicitly automated rehearsal, never impersonating team speakers."""
from pathlib import Path
import json,subprocess,wave
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parent/'ADA PROJECT DELIVERABLES';out=DEST/'05_Video';work=DEST/'WORKING/video';work.mkdir(parents=True,exist_ok=True)
segments=json.loads((out/'narration_segments.json').read_text())
assert len(segments)==8
chapters=['Problem and scope','Literature and question','Paired experimental design','Independent-control evidence','Paired contrasts','Daily-data feasibility','Scientific limitations','Reproducibility and conclusion']
suggested=['Mirunjai','Mirunjai','Mirunjai','Deeptanshu','Deeptanshu','Preksha','Preksha','Sudarshan']
manifest=[];elapsed=0.;transcript=['# Recording script - 3 to 5 minutes\n\nThe MP4 is an automated narration rehearsal using a standard synthetic voice. It does not contain recordings of the team. The final-week plan requires all members to speak: replace the rehearsal audio with the suggested member recordings below. No speaker identity is impersonated. The PPT speaker notes contain the same text.\n']
for i,text in enumerate(segments,1):
 script=work/f'segment_{i:02d}.txt';script.write_text(text)
 wav=work/f'segment_{i:02d}.wav'
 subprocess.run(['espeak-ng','-v','en-in','-s','175','-f',str(script),'-w',str(wav)],check=True)
 with wave.open(str(wav)) as w:seconds=w.getnframes()/w.getframerate()
 image=Path(f'/tmp/ada-slide-final-{i:02d}.png');assert image.exists()
 video=work/f'segment_{i:02d}.mp4'
 # Burn in the rehearsal attribution; standard voice, no copied human identity.
 vf="scale=1280:720,drawbox=x=0:y=690:w=1280:h=30:color=black@0.78:t=fill,drawtext=fontfile=/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf:text='AUTOMATED NARRATION REHEARSAL - replace with team recordings':fontcolor=white:fontsize=14:x=(w-text_w)/2:y=698"
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','12','-i',str(image),'-i',str(wav),'-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-ar','48000','-shortest',str(video)],check=True)
 record={'slide':i,'chapter':chapters[i-1],'suggested_speaker':suggested[i-1],'start_seconds':elapsed,'duration_seconds':seconds,'text':text};manifest.append(record)
 transcript.append(f"## Slide {i}: {chapters[i-1]}\n\nSuggested speaker: {suggested[i-1]}. Start {int(elapsed)//60:02d}:{int(elapsed)%60:02d}; about {seconds:.0f} seconds.\n\n{text}\n")
 elapsed+=seconds
concat=work/'segments.txt';concat.write_text(''.join("file '"+str(work/f'segment_{i:02d}.mp4')+"'\n" for i in range(1,9)))
final=out/'ADA_Project_Presentation_Rehearsal.mp4'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart','-metadata','title=ADA Project A - Automated Narration Rehearsal','-metadata','comment=EXPLORATORY. Standard synthetic voice; no team recordings or impersonation. Replace audio with all-member recordings before final submission.',str(final)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(final)]))
duration=float(probe['format']['duration']);assert 180<=duration<=300,duration
(out/'Recording_Script.md').write_text('\n'.join(transcript))
(out/'timing_manifest.json').write_text(json.dumps({'kind':'AUTOMATED REHEARSAL','duration_seconds':duration,'all_member_recordings_present':False,'segments':manifest},indent=2)+'\n')
(out/'video_validation.json').write_text(json.dumps(probe,indent=2)+'\n')
print(json.dumps({'video':str(final),'duration_seconds':duration,'rehearsal_only':True}))
