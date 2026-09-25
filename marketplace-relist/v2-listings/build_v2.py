import json,csv,os,re,shutil,sys,glob
import numpy as np
from PIL import Image,ImageOps,ImageFilter
S='/tmp/claude-0/-home-user-game/72a86570-ab34-5992-877c-c5e0835db40a/scratchpad'
sys.path.insert(0,S)
from listing_copy import C,MISSING
OUT='/home/user/game/marketplace-relist/v2-listings'
PKG=S+'/newfmt/Marketplace-Listing-Review-for-Claude-under-30MB'
inv={x['stock_range']:x for x in json.load(open(S+'/inventory_all.json')) if isinstance(x,dict) and 'stock_range' in x}
dec={r['stock']:r for r in csv.DictReader(open(PKG+'/Review-decisions.csv',encoding='utf-8-sig'))}
order=json.load(open(S+'/order.json'))
ROT=json.load(open(S+'/rot.json')) if os.path.exists(S+'/rot.json') else {}

C['092']=("Rohl 1983 Bar/Prep Faucet, Satin Nickel - New (R7514SLMSTN-2)","Rohl 1983 single-hole bar and prep faucet in satin nickel, single lever. 1.8 GPM.",[],"Kitchen")

# cover crop boxes (x0,y0,x1,y1) as fractions of the photo; the result is padded to a square
BOX={'027':(0,.08,1,.83),'028':(0,.25,1,1),'029':(0,.05,1,.8),'030':(0,.1,1,.85),'031':(0,.05,1,.7),'032':(0,.1,1,.85),
'033':(0,.05,1,.65),'034':(0,.2,1,.95),'035':(.05,.1,.95,.77),'036':(.2,.1,.85,1),'037':(0,0,1,1),'038':(.25,0,.95,1),
'039':(0,0,1,.75),'040':(.05,0,.85,1),'041':(0,.05,1,.8),'042':(.05,.05,.95,.72),'043':(.02,0,.92,.68),'044':(.05,.08,1,.8),
'045':(.2,.25,.8,.7),'046':(.2,.2,.8,.65),'047':(0,.05,.95,.72),'048':(0,.05,1,.8),'049':(0,.3,1,.85),'050':(.2,0,1,1),
'051':(.25,0,.9,1),'052':(.1,0,.85,1),'053':(0,.05,1,.8),'054':(.2,0,.85,1),'055':(0,.2,1,.95),'056':(0,.15,1,.9),
'057':(.15,0,.9,1),'058':(.05,.1,.95,.78),'059':(0,.25,1,1),'060':(0,0,.75,1),'061':(0,.2,1,.95),'062':(0,.25,1,1),
'063':(0,0,1,.75),'064':(0,0,1,.75),'065':(0,.1,1,.85),'066':(0,.05,1,.8),'067':(0,.1,1,.85),'068':(0,.05,1,.8),
'069':(0,.15,1,.9),'070':(.1,0,.85,1),'071':(0,.05,1,.8),'072':(0,.15,1,.9),'073':(0,.2,1,.95),'074':(0,0,1,.75),
'075':(0,0,1,.75),'076':(0,.05,1,.8),'077':(0,.15,1,.55),'078':(0,.05,1,.8),'079':(0,.1,1,.85),'080':(0,.1,1,.85),
'081':(0,.25,1,1),'082':(0,.1,1,.85),'084':(0,.2,1,.95),'085':(0,.1,1,.85),'086':(0,.25,1,1),'087':(0,.1,1,.85),
'088':(0,.1,1,.85),'089':(.1,0,.9,1),'090':(0,.1,1,.85),'091':(0,.1,1,.85),'092':(0,0,1,.75),'093':(0,0,1,.75),
'094':(0,0,1,.8),'100':(0,0,1,.6),'101':(0,0,1,.75),'102':(0,.05,1,.8),'118':(0,.1,1,.85)}

WARM=('gold','bronze','brass','champagne','copper')   # finishes where white-balance correction could misstate the color
STRONG={'053','061','075','078','080','093','094'}
WEAK={'030','032','033','049','065','067'}
LONG={'049':'60-inch','050':'48-inch','051':'48-inch','077':'48-inch'}
GLASS={'085','086'}

def enhance(im,warm):
    """Real-photo corrections only: white balance (skipped for warm finishes), levels, brightness, light sharpening."""
    a=np.asarray(im).astype(np.float32); log=[]
    if not warm:
        lum=a.mean(2); m=(lum>np.percentile(lum,5))&(lum<np.percentile(lum,95))
        means=a[m].mean(0); g=means.mean()/means
        g=np.clip(1+0.5*(g-1),0.94,1.06)
        if np.abs(g-1).max()>0.01: a=a*g; log.append('white balance (neutralized color cast, max 6%)')
    a=np.clip(a,0,255); im=Image.fromarray(a.astype(np.uint8))
    im=ImageOps.autocontrast(im,cutoff=(0.3,0.3),preserve_tone=True); log.append('levels (auto-contrast, 0.3% clip)')
    L=np.asarray(im.convert('L')).mean()
    if L<125:
        gamma=max(0.75,np.log(135/255)/np.log(max(L,1)/255))
        lut=[int(255*((i/255)**gamma)) for i in range(256)]
        im=im.point(lut*3); log.append(f'brightened (gamma {gamma:.2f})')
    im=im.filter(ImageFilter.UnsharpMask(radius=1.5,percent=50,threshold=3)); log.append('light sharpening')
    return im,log

def square(im,box):
    W,H=im.size; x0,y0,x1,y1=box
    c=im.crop((int(x0*W),int(y0*H),int(x1*W),int(y1*H))); w,h=c.size; s=max(w,h)
    if abs(w-h)<=2: return c,'cropped to square'
    e=np.concatenate([np.asarray(c)[0],np.asarray(c)[-1],np.asarray(c)[:,0],np.asarray(c)[:,-1]])
    col=tuple(int(v) for v in np.median(e,0))
    bg=Image.new('RGB',(s,s),col); bg.paste(c,((s-w)//2,(s-h)//2))
    return bg,'cropped, then padded to a square with a plain border (no content added)'

USE=[(('cartridge',),"Replacement part for repairing a Graff faucet or valve."),(('kitchen faucet','bar/prep'),"Great for a kitchen remodel, bar sink or prep sink."),
 (('trim','valve','rough','diverter'),"For a shower or tub remodel or repair. Plumbers and contractors welcome."),
 (('drain','grate'),"For a tiled shower build or drain upgrade."),
 (('showerhead','hand shower','slide bar','shower bar','wall bar','hose','elbow','arm','nipple'),"An easy shower upgrade."),
 (('bathroom faucet','lavatory','sink','tub faucet','tub spout','wall-mount bath'),"Great for a bathroom remodel or vanity upgrade."),
 (('towel','hook','holder','lever','grab bar','medicine','handle','coupling'),"Bathroom hardware for a remodel or quick refresh.")]
def use_line(t):
    t=t.lower()
    for keys,line in USE:
        if any(k in t for k in keys): return line
    return ""
STOCKDIR=PKG+'/Listing-folders'
STOCK_SKIP={'086':'image carries "for representation only" text and cabinet contents are unchecked','097':'image finish looks gold/champagne, not satin nickel'}
BOXCOVER={'030','032','033','034','049','060','065','067','070','076','077','081','088','089','090','091','095','096','097','098','099','100','102'}
def stock_image(src):
    im=Image.open(src).convert('RGB'); s=1080
    k=min(s*0.9/max(im.size),2.0); im=im.resize((int(im.width*k),int(im.height*k)),Image.LANCZOS)
    e=np.concatenate([np.asarray(im)[0],np.asarray(im)[-1]]); col=tuple(int(v) for v in np.median(e,0))
    bg=Image.new('RGB',(s,s),col); bg.paste(im,((s-im.width)//2,(s-im.height)//2)); return bg
def money(v): return f"${v:,.0f}"

for g in glob.glob(OUT+'/[123] - */'): shutil.rmtree(g)  # keep guide and images at the top level
rows=[]
for p in sorted(order):
    x=inv[p]; d=dec[p]; title,what,extra,cat=C[p]
    price=int(float(d['price'])); pnote=''
    if p in ('093','100'): price=499; pnote=f"Price set to $499: matches your website and fits under Meta's $500 limit for shipped items (package had ${d['price']})."
    if p=='092': price=499; pnote="Price set to $499 to match your website. The package had $475 (older override). Pick one."
    qty=int(d['quantity'])
    finish=(x.get('finish') or '').lower()
    warm=any(k in finish for k in WARM)
    hold = d['decision'] in ('HOLD','VERIFY IDENTITY') or p in WEAK
    group='1 - Post first' if p in STRONG else ('3 - Reshoot or verify first' if hold else '2 - Post next')
    if price>500: ship='local'
    elif p in LONG or p in GLASS: ship='local'
    elif price<40: ship='bundle'
    else: ship='both'
    if len(title)>70: title=re.sub(r' \([^)]*\)$','',title)
    cp=x.get('comparison') or {}
    L=[f"New, never installed. {what}"]
    u=use_line(title)
    if u: L.append(u)
    L+=["",f"Model: {x['model']}"]
    L+=extra
    if qty>1: L.append(f"{qty} available (price is each).")
    if cp.get('price') and cp.get('seller') and 'workbook' not in cp['seller'].lower():
        dt=cp.get('date','')
        L.append(f"Retail at {cp['seller']}: {money(cp['price'])} (checked {'Sep' if dt[5:7]=='09' else dt[5:7]} {int(dt[8:10])}, {dt[:4]}). My price: {money(price)}.")
    stock=f"{STOCKDIR}/REF_{p}/REFERENCE_ONLY_STOCK_IMAGE.jpg"
    has_stock=os.path.exists(stock) and p not in STOCK_SKIP
    spos=(2 if p in BOXCOVER else len(order[p])+1) if has_stock else None
    if has_stock: L+=["",f"Photo {spos} is the manufacturer's product image for reference. All other photos show the actual item."]
    else: L+=["","Photos are of the actual item."]
    L.append({'both':"Pickup in Gilbert, AZ by appointment, or shipped with tracking.",
              'local':"Local pickup in Gilbert, AZ by appointment.",
              'bundle':"Pickup in Gilbert, AZ by appointment. Can ship together with other items; ask for a bundle price."}[ship])
    L+=["Reasonable offers welcome. Bundle discount on 3 or more items.","Message me with any questions or for more photos.",f"Ref #{p}"]
    desc="\n".join(L)
    short=re.sub(r'[^A-Za-z0-9 ]+','',x.get('short_name',''))[:38].strip()
    folder=f"{OUT}/{group}/{p} {x['brand'].split(' /')[0].title()} {short} - ${price}"
    os.makedirs(folder,exist_ok=True)
    edits=[]
    seq=list(order[p])
    if has_stock: seq.insert(spos-1,'STOCK')
    for i,name in enumerate(seq,1):
        if name=='STOCK':
            stock_image(stock).save(f"{folder}/{i:02d}.jpg",quality=92)
            edits.append(f"{i:02d}.jpg  = manufacturer product image (from your package's stock reference, used with your permission); resized onto a square canvas, not otherwise edited")
            continue
        im=ImageOps.exif_transpose(Image.open(f"{S}/raw/{name}.jpg")).convert('RGB')
        e=[]
        r=ROT.get(name)
        if r: im=im.rotate(r,expand=True); e.append(f'rotated {r} degrees so it reads upright')
        if i==1:
            im,how=square(im,BOX.get(p,(0,0,1,1) if im.width>im.height else (0,.125,1,.875))); e.append(how)
        im,log=enhance(im,warm); e+=log
        if warm: e.append('white balance left alone to keep the true finish color')
        im.thumbnail((2048,2048),Image.LANCZOS)
        im.save(f"{folder}/{i:02d}.jpg",quality=90,optimize=True)
        edits.append(f"{i:02d}.jpg  (from your photo {name}.jpg): "+'; '.join(e))
    shipnote={'both':"Turn shipping ON in the listing's delivery options (and keep local pickup on). Weigh the packed box before you pick the label weight.",
              'local':"Leave shipping OFF (local pickup only). "+("It is over Meta's $500 limit for shipped items." if price>500 else "Too long or too fragile to ship profitably."),
              'bundle':"Leave shipping OFF on its own; low price. Ship only as part of a bundle."}[ship]
    notes=[f"Group: {group}.",f"Package decision: {d['decision']}. {d['reason']}",f"Shipping: {shipnote}"]
    if pnote: notes.append(pnote)
    if d['price_note'] and p not in ('092','093','100'): notes.append("Price check: "+d['price_note'])
    if p in STOCK_SKIP: notes.append("Stock image NOT added: "+STOCK_SKIP[p]+".")
    if has_stock: notes.append(f"Photo {spos:02d}.jpg is the manufacturer image. "+("It is 2nd because your cover is still a box, so buyers see the product right away. " if spos==2 else "It is last so your real photo stays the cover. ")+"Do not make it the cover.")
    if p in MISSING: notes.append("Check: "+MISSING[p])
    if p in WEAK: notes.append("Cover is still the box or tray, and no better photo exists. Take a new photo of the product out of the box before posting.")
    if d['facebook_url']: notes.append(f"Current listing: {d['facebook_url']} ({d['archived_status']})")
    txt=(f"TITLE\n{title}\n\nPRICE\n{price}\n\nCATEGORY\nHome Improvement Supplies\n\nCONDITION\nNew\n\nDESCRIPTION\n{desc}\n\n"
         f"PHOTOS\nUpload {', '.join(f'{i:02d}.jpg' for i in range(1,len(order[p])+1+(1 if has_stock else 0)))} in that order. 01.jpg is the square cover.\n\n"
         "----- NOTES FOR YOU (do not paste) -----\n"+"\n".join(notes)+"\n\nPHOTO EDITS (nothing AI-generated):\n"+"\n".join(edits)+"\n")
    open(f"{folder}/LISTING.txt",'w').write(txt)
    rows.append(dict(ref=p,group=group,title=title,title_chars=len(title),price=price,qty=qty,shipping=ship,photos=len(order[p]),folder=os.path.relpath(folder,OUT)))
w=csv.DictWriter(open(f"{OUT}/INDEX.csv",'w',newline=''),fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
from collections import Counter
print(Counter(r['group'] for r in rows),Counter(r['shipping'] for r in rows),max(r['title_chars'] for r in rows))
