from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse, json, subprocess
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--font',default='/System/Library/Fonts/STHeiti Light.ttc');p.add_argument('--sky',action='store_true',help='Cloud background without labels');args=p.parse_args()
font=None if args.sky else ImageFont.truetype(args.font,16)
sky=Image.open(ROOT/'assets/sky-background.png').convert('RGB').resize((1280,720),Image.Resampling.LANCZOS) if args.sky else None
BG=(247,247,244);atlas=Image.open(ROOT/'assets/spritesheet.png').convert('RGBA')
spec=[('待机','Idle',[560,220,220,280,280,640]),('向右慢走','Walk right',[240]*7+[440]),('向左慢走','Walk left',[240]*7+[440]),('轻轻招手','Wave',[280]*3+[560]),('小小跳跃','Little hop',[280]*4+[560]),('蹭毯安慰','Blanket comfort',[280]*7+[480]),('等待回应','Waiting',[300]*5+[520]),('整理毛毯','Tend the blanket',[240]*5+[440]),('检查毛毯','Check the blanket',[300]*5+[560]),('十六方向环视','Look around',[400]*16)]
spec=[(zh,en,[d//2 for d in ds]) for zh,en,ds in spec]
frames=[]
for r,(_,_,ds) in enumerate(spec):
 frames.append([atlas.crop(((i%8)*192,(r+i//8)*208,(i%8+1)*192,(r+i//8+1)*208)) for i in range(len(ds))])
length=6400;step=20
out=ROOT/'previews';out.mkdir(exist_ok=True)
def frame_at(t,lang):
 c=sky.copy() if args.sky else Image.new('RGB',(1280,576),BG);draw=ImageDraw.Draw(c)
 for r,(zh,en,ds) in enumerate(spec):
  period=sum(ds);local=t%period
  i=0
  while local>=ds[i] and i<len(ds)-1:local-=ds[i];i+=1
  x=(r%5)*256;y=(r//5)*288
  c.paste(frames[r][i],(x+32,y+(152 if args.sky else 24)),frames[r][i])
  if not args.sky:draw.text((x+128,y+251),zh if lang=='zh' else en,font=font,fill=(67,66,63),anchor='mm')
 return c
for lang in (['sky'] if args.sky else ['zh','en']):
 palette=frame_at(0,lang).quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 indexed=[frame_at(t,lang).quantize(palette=palette,dither=Image.Dither.NONE) for t in range(0,length,step)]
 gif=out/f'grid-{lang}.gif'
 indexed[0].save(gif,save_all=True,append_images=indexed[1:],duration=step,loop=0,disposal=1,optimize=False)
 frame_at(500,lang).save(out/f'grid-{lang}.png')
 subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-i',str(gif),'-vf','fps=50,format=yuv420p','-c:v','libx264','-crf','16','-movflags','+faststart',str(out/f'grid-{lang}.mp4')],check=True)
 print(gif, gif.stat().st_size)
(out/('timing-sky.json' if args.sky else 'timing.json')).write_text(json.dumps({'duration_ms':length,'frame_step_ms':step,'layout':'5 columns x 2 rows','actions':[{'zh':zh,'en':en,'frame_durations_ms':ds,'cycle_ms':sum(ds)} for zh,en,ds in spec]},ensure_ascii=False,indent=2))
