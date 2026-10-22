"""Patch the embedded detector for the 16:10 profile.

Reads the detector module from base/base_branded.exe, lowers the first-arm HUD
thresholds, replaces normalize_top with the custom-size version, and makes the
inventory tab row robust to the Tarkov 1.0 layout shift. Writes detector.marshal
for repack_pyz.py.
"""
import base64
import marshal
import struct
import types
import zlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "base" / "base_branded.exe"
OUT = BASE / "detector.marshal"
COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"
SLOT = 15392  # compressed detector slot inside the PYZ

REPLACE = {0.48: 0.30, 0.45: 0.28, 0.22: 0.12}

# Page templates are normalized to the detector's 1920x240 top strip. They are
# embedded in the module as base64 PNGs so the rebuild does not need to add
# separate CArchive entries.
IFACE_TEMPLATES = {
    "A": ("hotbar_A.png", (565, 0, 1500, 90)),
    "B": ("tabs_B.png", (0, 0, 800, 36)),
    "C": ("tabs_C.png", (0, 0, 800, 36)),
    "D": ("tabs_D.png", (0, 0, 800, 36)),
    "E": ("tabs_E.png", (0, 0, 800, 36)),
    "F": ("tabs_F.png", (0, 0, 800, 36)),
    "G": ("tabs_G.png", (0, 0, 800, 36)),
    "O": ("tabs_O.png", (0, 0, 800, 36)),
    "P": ("console_P.png", (0, 0, 700, 26)),
    "Q": ("pause_Q.png", (440, 55, 1450, 240)),
    # The post-raid result screen keeps the same centered title for every
    # outcome (survived, died, extracted early). Treat it as a safe page so
    # the HUD-absence gate cannot send Alt+F4 while the result is on screen.
    "Y": ("result_Y.png", (840, 0, 1120, 100)),
    # The lobby logo floats over a rotating background and changes position
    # and scale between sessions. This crop of the word ESCAPE is matched at
    # several scales instead of using one fixed box.
    "Q2": ("home_Q.png", (0, 0, 1920, 240)),
}


def interface_blobs():
    blobs = {}
    boxes = {}
    root = BASE / "assets" / "interface"
    for key, (name, box) in IFACE_TEMPLATES.items():
        data = (root / name).read_bytes()
        blobs[key] = base64.b64encode(data).decode("ascii")
        boxes[key] = box
    return blobs, boxes

NORMALIZE_SOURCE = '''
def normalize_top(self, frame, full_size=None):
    h,w=frame.shape[:2]
    full_w,full_h=full_size or (w,h)
    custom=getattr(self,'custom_size',None)
    if custom:
        if full_size is not None and (full_w,full_h)!=tuple(custom):
            raise ValueError('Configured resolution does not match game area')
        if w!=full_w:
            raise ValueError('Configured resolution does not match game area')
    elif w!=full_w or abs(full_w/full_h-1.6888888888888889)>0.1:
        raise ValueError('Only 16:10 game area supported by this HUD profile')
    strip_h=round(full_h*240/1080)
    if h<strip_h:raise ValueError('Capture strip is too short')
    top=cv2.resize(frame[:strip_h],(1920,240))
    if top.shape[2]==4:
        top=cv2.cvtColor(top,cv2.COLOR_BGRA2BGR)
    return top
'''

SCORES_SOURCE = '''
def scores_top(self, top):
    health,_ = features(top)
    color=float(np.mean(cv2.dilate(health,np.ones((3,3),np.uint8))[self.masks[0]>0]>0))
    gray=cv2.cvtColor(cv2.resize(top[15:235,20:115],(48,110)),cv2.COLOR_BGR2GRAY)
    body=self.oriented_support(gray,self.body_mask,self.body_bins)
    gray_bar=cv2.cvtColor(cv2.resize(top[1:80,565:1500],(468,40)),cv2.COLOR_BGR2GRAY)
    gx=cv2.Sobel(gray_bar,cv2.CV_32F,1,0);gy=cv2.Sobel(gray_bar,cv2.CV_32F,0,1)
    edges=cv2.Canny(gray_bar,35,90)
    horizontal=np.where(np.abs(gy)>=np.abs(gx)*1.5,edges,0).astype('uint8')
    vertical=np.where(np.abs(gx)>=np.abs(gy)*1.5,edges,0).astype('uint8')
    def bar_support(edges,reference):
        # The hotbar sits 1-2 px higher on some HUD scales. A slightly wider
        # distance tolerance keeps the same template usable without matching
        # menu pages (their support stays below 0.05).
        if not np.any(edges):return 0.
        distance=cv2.distanceTransform(255-edges,cv2.DIST_L2,3)
        values=distance[reference>0]
        return float(np.mean(np.maximum(0,1-values/2.2))) if len(values) else 0.
    hs=bar_support(horizontal,self.bar_h)
    vs=bar_support(vertical,self.bar_v)
    frames=min(hs,vs)  # both directions, not just one weapon/road edge
    labels=self.distance_support(cv2.Canny(cv2.cvtColor(cv2.resize(top[8:32,575:1195],(310,12)),cv2.COLOR_BGR2GRAY),35,90),self.labels)
    total=.20*body+.45*frames+.30*labels+.05*color
    self.last_features=dict(body_shape=body,bar_frames=frames,label_shape=labels,color=color,combat_score=total)
    return body,.58*frames+.42*labels
'''

EXTRACTION_SOURCE = r'''
def extraction_features(self,top):
    scene_luma=float(cv2.cvtColor(top[100:230,200:1600],cv2.COLOR_BGR2GRAY).mean())
    hsv=cv2.cvtColor(top[3:58,1345:1775],cv2.COLOR_BGR2HSV)
    green=float(np.mean((hsv[:,:,0]>20)&(hsv[:,:,0]<50)&(hsv[:,:,1]>100)&(hsv[:,:,2]>100)))
    title=zero=raw_zero=0.
    timer=dict(state='unknown',zero_score=0.,digits=[],scores=[],margins=[])
    if green>.55:
        gray=cv2.cvtColor(top[3:56,1340:1660],cv2.COLOR_BGR2GRAY)
        base=self.extract_title
        # The 16:10 strip compresses the banner vertically. Matching a few
        # nearby heights keeps one template valid for 16:9 and 16:10.
        for height in (base.shape[0]-6,base.shape[0]-4,base.shape[0]-2,
                base.shape[0],base.shape[0]+2):
            if height<8 or height>gray.shape[0]:continue
            template=(base if height==base.shape[0] else
                cv2.resize(base,(base.shape[1],height),interpolation=cv2.INTER_LINEAR))
            if template.shape[1]>gray.shape[1]:continue
            title=max(title,float(cv2.minMaxLoc(cv2.matchTemplate(gray,template,cv2.TM_CCOEFF_NORMED))[1]))
        # Locate the red countdown by its ink instead of a fixed crop. The
        # timer sits immediately right of the banner on the current HUD (the
        # old build looked below it). Only the rightmost two glyphs matter.
        def digit_glyphs(box):
            b,g,r=cv2.split(box)
            r=r.astype('int16');g=g.astype('int16');b=b.astype('int16')
            mask=((r>45)&(r-g>18)&(r-b>18)).astype('uint8')*255
            count,labels,stats,_=cv2.connectedComponentsWithStats(mask)
            found=[]
            for i in range(1,count):
                x,y,w,h,area=map(int,stats[i])
                if not (h>=7 and w>=3 and area>=14 and h<=30 and w<=40):continue
                piece=np.where(labels[y:y+h,x:x+w]==i,255,0).astype('uint8')
                parts=[(0,w,piece)]
                # Bloom can join neighboring glyphs. Split a wide component at
                # the lowest-ink column near its middle before normalizing.
                if w>20 and h>=10:
                    projection=piece.sum(axis=0)
                    middle=w//2
                    cut=min(range(max(2,middle-5),min(w-2,middle+6)),
                        key=lambda column:(float(projection[column]),abs(column-middle)))
                    parts=[(0,cut,piece[:,:cut]),(cut,w,piece[:,cut:])]
                for left,right,part in parts:
                    ys,xs=np.where(part>0)
                    if len(xs)==0:continue
                    px,py=xs.min(),ys.min()
                    pw,ph=xs.max()-xs.min()+1,ys.max()-ys.min()+1
                    glyph=np.where(part[py:py+ph,px:px+pw]>0,255,0).astype('uint8')
                    normalized=cv2.resize(glyph,(20,28),interpolation=cv2.INTER_LINEAR).astype('float32')/255
                    found.append((x+left+px,y+py,pw,ph,normalized,float(pw/ph)))
            found.sort(key=lambda item:item[0])
            return found
        def classify(glyphs):
            digits=[];scores=[];margins=[];zeros=[]
            for _,_,_,_,image,ratio in glyphs:
                by_label={}
                for label,reference,reference_ratio in self.timer_digits.templates:
                    if abs(ratio-reference_ratio)>.20:score=0.
                    else:
                        cosine=float(np.sum(image*reference)/(np.linalg.norm(image)*np.linalg.norm(reference)+1e-6))
                        score=.55*cosine+.45*(1-float(np.mean(np.abs(image-reference))))
                    by_label[label]=max(by_label.get(label,0.),score)
                ranked=sorted(by_label.items(),key=lambda pair:pair[1],reverse=True)
                digits.append(ranked[0][0]);scores.append(ranked[0][1])
                margins.append(ranked[0][1]-ranked[1][1]);zeros.append(by_label.get(0,0.))
            return digits,scores,margins,zeros
        # The banner-right band is the current layout. The lower band keeps
        # the previous layout usable without mixing both rows into one read.
        for box in (top[5:58,1760:1915],top[60:110,1830:1900]):
            glyphs=digit_glyphs(box)
            if len(glyphs)<2:continue
            left,right=glyphs[-2:]
            if abs(left[1]-right[1])>5:continue
            gap=right[0]-(left[0]+left[2])
            if gap<0 or gap>12:continue
            digits,scores,margins,zeros=classify((left,right))
            # Both rightmost glyphs must be a confident 0. 8/6/9 do not reach
            # the 0.93 score, so they remain a nonzero countdown.
            zero_ok=digits==[0,0] and all(score>=.93 and margin>=.035
                for score,margin in zip(scores,margins))
            timer=dict(state='zero' if zero_ok else 'nonzero',
                zero_score=min(zeros) if digits==[0,0] else 0.,
                digits=digits,scores=scores,margins=margins)
            break
        zero=timer['zero_score']
        # Kept for log compatibility; the glyph reader above is authoritative.
        raw_zero=zero
    banner=green>.55 and title>=.65
    if banner:
        # Remember the last valid extraction banner. The post-raid result
        # screen is only treated as a safe Y page while this evidence is
        # recent, so a death result still follows the normal Alt+F4 gate.
        self.last_extraction_seen=time.perf_counter()
    return dict(banner=banner,green_fraction=green,title_score=title,zero_score=zero,raw_zero_score=raw_zero,
        timer_state=timer['state'],timer_digits=timer['digits'],timer_scores=timer['scores'],timer_margins=timer['margins'],scene_luma=scene_luma)
'''

GUARD_SOURCE = r'''
def update(self,now,combat_score,menu_present,cue):
    if not cue:
        self.reset('no_cue');return False
    # N returns a full menu score so the absence gate stays reset during the
    # extraction countdown. Do not let that same score wipe the extraction
    # tracker; otherwise zero evidence could never be confirmed.
    if menu_present and not cue.get('banner'):
        self.reset('menu_visible');return False
    luma=cue['scene_luma']
    if cue['banner']:
        self.track_countdown(now,cue,luma)
        self.fade_start=None;self.falling=0
        state=cue.get('timer_state','zero' if cue['zero_score']>=.93 else 'nonzero')
        if state=='zero' and cue['zero_score']<.93:state='unknown'
        if state=='zero' and cue['zero_score']>=.93:
            if self.zero_start is None:self.zero_start=now
            self.zero_last=now;self.zero_luma=luma
            if now-self.zero_start>=.15:self.zero_confirmed=True
            self.reason='zero_tracking'
        elif state=='unknown' and self.zero_confirmed and now-self.zero_last<=1.0:
            self.reason='zero_confirmed_digits_faded'
        else:
            self.zero_start=None;self.zero_last=None;self.zero_confirmed=False;self.reason='timer_unknown' if state=='unknown' else 'timer_nonzero'
        return False
    if self.fade_start is None:
        reason=None
        countdown_ok=(self.count_value is not None and self.count_value<=2 and self.count_steps>=2
            and now-self.count_start>=1.2 and now-self.count_last<=1.5
            and -.9<=now-(self.count_since+self.count_value)<=1.5)
        if self.zero_last is None and countdown_ok:
            self.zero_last=now;self.zero_confirmed=True;self.zero_luma=self.count_luma
        if self.zero_last is None:reason='zero_not_observed'
        elif now-self.zero_last>1.0:reason='zero_evidence_expired'
        elif not self.zero_confirmed:reason='zero_seen_too_briefly'
        elif combat_score<.48:reason='hud_not_confident_at_banner_end'
        if reason:
            self.reset(reason);return False
        self.fade_start=now;self.previous_luma=luma
    if now-self.fade_start>3.0 or combat_score<=.22:
        self.reset('fade_timeout' if now-self.fade_start>3.0 else 'hud_lost_before_fade_confirmation');return False
    if luma<=self.previous_luma+.02*max(self.zero_luma,1):self.falling+=1
    else:self.falling=0
    self.previous_luma=luma
    self.reason='waiting_fade'
    # Confirm while the combat HUD still exists. Sudden HUD loss before fade
    # confirmation remains a death candidate handled by Gate.
    if now-self.fade_start>=.20 and self.falling>=3 and combat_score>=.48 and luma<=self.zero_luma*.65:
        record=dict(fade_seconds=now-self.fade_start,baseline_luma=self.zero_luma,current_luma=luma,combat_score=combat_score)
        self.reset('confirmed');self.last_confirmation=record;return True
    return False
'''

MENU_SOURCE = r'''
def menu_score_top(self, top):
    # Treat every documented game interface as a safe page. Each page is
    # recognized by its own normalized template, so the HUD-absence gate is
    # reset and no Alt+F4 is sent while that page is visible. The extraction
    # page (N) is also protected while its banner is visible; ExtractionGuard
    # ignores menu_present for N so the countdown can still be tracked.
    gray=cv2.cvtColor(top,cv2.COLOR_BGR2GRAY)
    if not hasattr(self,'iface_templates'):
        import base64
        blobs=__IFACE_BLOBS__
        boxes=__IFACE_BOXES__
        self.iface_templates={key:cv2.imdecode(np.frombuffer(base64.b64decode(value),np.uint8),0)
            for key,value in blobs.items()}
        self.iface_boxes=boxes
    def correlation(box,template,margin_x=2,margin_y=2):
        x1,y1,x2,y2=box
        region=gray[max(0,y1-margin_y):min(gray.shape[0],y2+margin_y),max(0,x1-margin_x):x2+margin_x]
        return max(0.,float(cv2.minMaxLoc(cv2.matchTemplate(region,template,cv2.TM_CCOEFF_NORMED))[1]))
    # The post-raid result title shares the same centered box as the
    # confirmation dialog. Match it before the other page anchors so a
    # successful extraction is never mistaken for a missing HUD on the
    # results screen (which would close the game with Alt+F4).
    result_score=correlation(self.iface_boxes['Y'],self.iface_templates['Y'],2,2)
    extraction_seen=getattr(self,'last_extraction_seen',None)
    recent_extraction=(extraction_seen is not None
        and time.perf_counter()-extraction_seen<=60.)
    if result_score>=.58 and recent_extraction:
        # Refresh while the result stays visible so reading the summary for
        # longer than the 60 s window cannot re-enable the Alt+F4 gate.
        self.last_extraction_seen=time.perf_counter()
        self.last_interface='Y'
        self.last_menu_features=dict(interface='Y',interface_score=result_score,
            result=result_score,recent_extraction=True,
            inventory=0.,settings=0.,pause=0.,confirmation=0.,
            skipped_for_combat=False,extraction_banner=False,
            console_features=dict(present=False))
        return 1.
    features=getattr(self,'last_features',{}) or {}
    extraction=getattr(self,'last_extraction',{}) or {}
    extraction_banner=bool(extraction.get('banner'))
    console=self.console_header(gray)
    console_template=correlation(self.iface_boxes['P'],self.iface_templates['P'],8,8)
    if console_template>=.64 or console['present']:
        self.last_interface='P'
        self.last_menu_features=dict(interface='P',interface_score=console_template,console=1.,
            console_features=console,inventory=0.,settings=0.,pause=0.,confirmation=0.,skipped_for_combat=False)
        return 1.
    tab_scores={key:correlation(self.iface_boxes[key],self.iface_templates[key],10,8)
        for key in ('B','C','D','E','F','G','O')}
    best_tab=max(tab_scores,key=tab_scores.get)
    tab_score=tab_scores[best_tab]
    inv_edge=self.distance_support(cv2.Canny(gray[14:40,280:850],35,90),self.inventory_edges)
    inv_return=self.distance_support(cv2.Canny(gray[4:36,1740:1840],35,90),self.inventory_return_edges)
    inv_template=correlation((280,12,850,38),self.menu_templates[0],2,8)
    inventory=max(.90*inv_edge+.10*inv_return if inv_edge>=.60 else 0.,inv_template if inv_template>=.62 else 0.)
    tab_interface=''
    if tab_score>=.65:
        inventory=1.;tab_interface=best_tab
    elif inv_return>=.48 and inv_edge>=.30:
        # Prestige/unlisted tab: the shared return label and tab row are present
        # even when no per-tab reference matches.
        inventory=max(inventory,.90);tab_interface='H'
    settings_title=correlation((840,5,1010,65),self.extra_menu_templates['settings_title'])
    settings_return=self.distance_support(cv2.Canny(gray[25:78,1765:1845],35,90),self.settings_return_edges)
    settings=min(settings_title,settings_return)
    pause_left=correlation((530,125,1030,180),self.extra_menu_templates['pause_logo_left'],48,35)
    pause_right=correlation((1040,125,1290,180),self.extra_menu_templates['pause_logo_right'],48,35)
    pause=min(pause_left,pause_right)
    pause_template=correlation(self.iface_boxes['Q'],self.iface_templates['Q'],8,8)
    if pause_template>=.62:pause=max(pause,pause_template)
    confirm_title=correlation((875,18,1045,58),self.extra_menu_templates['confirm_title'])
    confirm_subtitle=correlation((905,58,1020,80),self.extra_menu_templates['confirm_subtitle'])
    confirmation=min(confirm_title,confirm_subtitle)
    hotbar_template=correlation(self.iface_boxes['A'],self.iface_templates['A'],10,8)
    hotbar_safe=(not extraction_banner and hotbar_template>=.78
        and features.get('body_shape',0)>=.25 and features.get('label_shape',0)>=.30
        and features.get('combat_score',0)<.48)
    # The lobby main menu animates its logo, so the fixed pause box only
    # matches one pose. Match the bright ESCAPE word across the whole strip
    # and a few scales. Skip the search when a cheaper page or combat HUD
    # already explains the frame; the half-resolution search is ~16 ms.
    home_score=0.
    home_template=self.iface_templates.get('Q2')
    if (home_template is not None and not tab_interface and settings<.55
            and pause<.80 and confirmation<.55 and not hotbar_safe
            and not extraction_banner and features.get('combat_score',0)<=.22):
        if not hasattr(self,'home_variants'):
            base=cv2.resize(home_template,(max(1,home_template.shape[1]//2),
                max(1,home_template.shape[0]//2)),interpolation=cv2.INTER_AREA)
            self.home_variants=[cv2.resize(base,
                (max(1,int(base.shape[1]*scale)),
                 max(1,int(base.shape[0]*scale*aspect))),
                interpolation=cv2.INTER_AREA)
                for aspect in (1.,1.25,1.5)
                for scale in (.85,.95,1.05,1.15)]
            self.home_small=(960,120)
        small=cv2.resize(gray,self.home_small,interpolation=cv2.INTER_AREA)
        for variant in self.home_variants:
            if variant.shape[0]>small.shape[0] or variant.shape[1]>small.shape[1]:continue
            home_score=max(home_score,float(cv2.minMaxLoc(
                cv2.matchTemplate(small,variant,cv2.TM_CCOEFF_NORMED))[1]))
        if home_score>=.66:pause=max(pause,home_score)
    if tab_interface:
        interface=tab_interface
    elif settings>=.55:
        interface='S'
    elif pause>=.55:
        interface='Q'
    elif confirmation>=.55:
        interface='K'
    elif hotbar_safe:
        interface='A'
    elif extraction_banner:
        interface='N'
    elif features.get('combat_score',0)>.22:
        interface='X'
    else:
        interface='0'
    if interface=='Q':
        # Back in the lobby after a raid; the next result screen belongs to a
        # new raid and must not inherit the previous extraction protection.
        self.last_extraction_seen=None
    self.last_interface=interface
    # A is an in-raid HUD, not a menu. Its whitelist only matters when combat
    # evidence is weak; a confident combat score already keeps the gate reset.
    # N is protected for as long as the extraction banner is recognized, so a
    # red countdown or a bright HUD cannot turn into an Alt+F4.
    menu=max(inventory,settings,pause,confirmation,
        1. if interface=='N' else 0.,
        1. if hotbar_safe and features.get('combat_score',0)<=.22 else 0.)
    if interface=='A':interface_score=hotbar_template
    elif tab_interface:interface_score=tab_score
    elif interface=='Q':interface_score=max(pause_template,home_score)
    else:interface_score=menu
    self.last_menu_features=dict(interface=interface,interface_score=interface_score,
        inventory=inventory,settings=settings,pause=pause,confirmation=confirmation,
        inventory_nav=inv_edge,inventory_return=inv_return,inventory_template=inv_template,
        settings_title=settings_title,settings_return=settings_return,pause_left=pause_left,pause_right=pause_right,
        pause_template=pause_template,home_score=home_score,confirm_title=confirm_title,confirm_subtitle=confirm_subtitle,
        hotbar_template=hotbar_template,tab_scores=tab_scores,tab_match=best_tab,
        extraction_banner=extraction_banner,skipped_for_combat=False,console_features=console)
    return menu
'''

ANALYZE_SOURCE = r'''
def analyze(self, frame, full_size=None):
    top=self.normalize_top(frame,full_size)
    self.last_top=top
    self.last_extraction=self.extraction_features(top)
    scores=self.scores_top(top)
    # The extraction banner is a protected state even when the HUD is bright
    # enough for the combat early-return. ExtractionGuard ignores this menu
    # score while the banner is up, so the countdown still tracks to zero.
    if self.last_extraction.get('banner'):
        self.last_interface='N'
        self.last_menu_features=dict(interface='N',interface_score=1.,inventory=0.,settings=0.,
            pause=0.,confirmation=0.,skipped_for_combat=False,extraction_banner=True)
        return scores,1.
    if self.last_features['combat_score']>=.48:
        self.last_interface='X'
        self.last_menu_features=dict(inventory=0.,settings=0.,pause=0.,confirmation=0.,
            skipped_for_combat=True,interface='X',interface_score=self.last_features['combat_score'])
        return scores,0.
    return scores,self.menu_score_top(top)
'''


def parse_archive(buf):
    cp = buf.rfind(COOKIE)
    if cp < 0:
        raise RuntimeError("cookie not found")
    magic, pkg_len, toc_off, toc_len, pyver, pylib = struct.unpack(
        "!8sIIii64s", buf[cp:cp + 88]
    )
    tail = len(buf) - cp - 88
    overlay = len(buf) - (pkg_len + tail)
    toc = bytes(buf[overlay + toc_off:overlay + toc_off + toc_len])
    entries = {}
    pos = 0
    while pos < len(toc):
        es, = struct.unpack("!i", toc[pos:pos + 4])
        epos, cmprsd, uncmprsd, flag, typ, name = struct.unpack(
            "!IIIBc" + str(es - 18) + "s", toc[pos + 4:pos + es]
        )
        nm = name.decode("utf-8", "replace").rstrip("\0")
        entries[nm] = {
            "pos": epos, "cmprsd": cmprsd, "uncmprsd": uncmprsd,
            "flag": flag, "type": typ,
        }
        pos += es
    return overlay, entries


def find_code(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            found = find_code(const, name)
            if found is not None:
                return found
    return None


def find_class_method(code, class_name, method_name):
    for value in code.co_consts:
        if isinstance(value, types.CodeType) and value.co_name == class_name:
            for item in value.co_consts:
                if isinstance(item, types.CodeType) and item.co_name == method_name:
                    return item
    return None


def patch_consts(code):
    changed = []
    consts = []
    for value in code.co_consts:
        if isinstance(value, float) and value in REPLACE:
            consts.append(REPLACE[value])
            changed.append((value, REPLACE[value]))
        else:
            consts.append(value)
    if not changed:
        raise RuntimeError("no threshold constants replaced")
    return code.replace(co_consts=tuple(consts)), changed


def replace_code(code, name, new):
    consts = []
    hit = False
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            if value.co_name == name:
                consts.append(new)
                hit = True
            else:
                replaced, found = replace_code(value, name, new)
                consts.append(replaced)
                hit = hit or found
        else:
            consts.append(value)
    return code.replace(co_consts=tuple(consts)), hit


def replace_class_method(code, class_name, method_name, new):
    """Replace a method inside one class only.

    Gate.update and ExtractionGuard.update share the same code name, so the
    generic replace_code helper cannot be used for either guard.
    """
    consts = []
    hit = False
    for value in code.co_consts:
        if isinstance(value, types.CodeType) and value.co_name == class_name:
            inner = []
            for item in value.co_consts:
                if isinstance(item, types.CodeType) and item.co_name == method_name:
                    inner.append(new)
                    hit = True
                else:
                    inner.append(item)
            consts.append(value.replace(co_consts=tuple(inner)))
        else:
            consts.append(value)
    return code.replace(co_consts=tuple(consts)), hit


buf = SRC.read_bytes()
overlay, entries = parse_archive(buf)
pyz = entries["PYZ.pyz"]
pyz_bytes = bytes(buf[overlay + pyz["pos"]:overlay + pyz["pos"] + pyz["cmprsd"]])
toc_pos = struct.unpack(">i", pyz_bytes[8:12])[0]
toc = dict(marshal.loads(pyz_bytes[toc_pos:]))
is_pkg, pos, length = toc["detector"]
if length != SLOT:
    print("warning: detector slot is", length, "expected", SLOT)
blob = zlib.decompress(pyz_bytes[pos:pos + length])
code = marshal.loads(blob)
func = find_code(code, "start_hud_evidence")
if func is None:
    raise RuntimeError("start_hud_evidence not found")

patched, changed = patch_consts(func)
compiled = compile(NORMALIZE_SOURCE, "detector.py", "exec")
new_normalize = find_code(compiled, "normalize_top")
if new_normalize is None:
    raise RuntimeError("normalize_top source compile failed")
new_scores = find_code(compile(SCORES_SOURCE, "detector.py", "exec"), "scores_top")
if new_scores is None:
    raise RuntimeError("scores_top source compile failed")
iface_blobs, iface_boxes = interface_blobs()
menu_source = MENU_SOURCE.replace("__IFACE_BLOBS__", repr(iface_blobs))
menu_source = menu_source.replace("__IFACE_BOXES__", repr(iface_boxes))
new_menu = find_code(compile(menu_source, "detector.py", "exec"), "menu_score_top")
if new_menu is None:
    raise RuntimeError("menu_score_top source compile failed")
new_analyze = find_code(compile(ANALYZE_SOURCE, "detector.py", "exec"), "analyze")
if new_analyze is None:
    raise RuntimeError("analyze source compile failed")
new_extract = find_code(
    compile(EXTRACTION_SOURCE, "detector.py", "exec"), "extraction_features"
)
if new_extract is None:
    raise RuntimeError("extraction_features source compile failed")
new_guard = find_code(compile(GUARD_SOURCE, "detector.py", "exec"), "update")
if new_guard is None:
    raise RuntimeError("ExtractionGuard.update source compile failed")
old_gate_update = find_class_method(code, "Gate", "update")
if old_gate_update is None:
    raise RuntimeError("Gate.update not found in the original module")

# Rebuild the module code object with all replacements applied in place.
module, hit_arm = replace_code(code, "start_hud_evidence", patched)
module, hit_norm = replace_code(module, "normalize_top", new_normalize)
module, hit_scores = replace_code(module, "scores_top", new_scores)
module, hit_menu = replace_code(module, "menu_score_top", new_menu)
module, hit_analyze = replace_code(module, "analyze", new_analyze)
module, hit_extract = replace_code(module, "extraction_features", new_extract)
module, hit_guard = replace_class_method(
    module, "ExtractionGuard", "update", new_guard
)
if not (hit_arm and hit_norm and hit_scores and hit_menu and hit_analyze
        and hit_extract and hit_guard):
    raise RuntimeError("detector functions not replaced")

# The two guards both define update(). Verify only ExtractionGuard changed.
if find_class_method(module, "ExtractionGuard", "update") is not new_guard:
    raise RuntimeError("ExtractionGuard.update was not replaced")
gate_update = find_class_method(module, "Gate", "update")
if (gate_update is None
        or gate_update.co_code != old_gate_update.co_code
        or gate_update.co_firstlineno != old_gate_update.co_firstlineno):
    raise RuntimeError("Gate.update was modified accidentally")
new_blob = marshal.dumps(module)

# Execute the patched function in isolation (it only uses features.get).
namespace = {"__builtins__": {}}
check = types.FunctionType(patched, namespace)
sample = {
    "body_shape": 0.31623741483105067,
    "bar_frames": 0.2993544638156891,
    "label_shape": 0.6750180125236511,
    "combat_score": 0.42809425535922097,
}
low = {
    "body_shape": 0.33865421278274993,
    "bar_frames": 0.27085378766059875,
    "label_shape": 0.6215365529060364,
    "combat_score": 0.3760760128756303,
}
assert check(sample) is True
assert check(low) is True
# Real 2026-10-22 frames repeatedly failed at bar_frames .148-.189 while every
# other HUD cue was stable. Keep them armable with the same body/label gate.
low_bar = {
    "body_shape": 0.3364,
    "bar_frames": 0.1490,
    "label_shape": 0.6623,
    "combat_score": 0.3330,
}
assert check(low_bar) is True
# A recorded inventory page must still stay far below the first-arm gate.
menu = {
    "body_shape": 0.0601,
    "bar_frames": 0.0069,
    "label_shape": 0.2701,
    "combat_score": 0.0978,
}
assert check(menu) is False

from zopfli.zlib import compress as deflate
packed = deflate(new_blob)
print("replaced", changed)
print("marshal", len(blob), "->", len(new_blob))
print("zopfli", len(packed), "slot", length, "headroom", length - len(packed))
if len(packed) > length:
    print("note: larger than the old slot; repack_pyz.py grows the PYZ data area")
OUT.write_bytes(new_blob)
print("written", OUT)
