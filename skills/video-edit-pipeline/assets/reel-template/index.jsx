import React from 'react';
import {
  AbsoluteFill, Composition, Img, OffthreadVideo, Sequence, interpolate,
  registerRoot, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';

const yellow = '#ffe348';
const shadow = '0 5px 0 #111, 0 8px 22px #000c';
const font = 'Arial, Helvetica, sans-serif';

function SourceVideo({source, style, muted}) {
  return <OffthreadVideo src={staticFile(source.src)} trimBefore={source.startFrame}
    trimAfter={source.endFrame} muted={muted ?? source.muted}
    style={{width: '100%', height: '100%', objectFit: 'cover',
      objectPosition: `${source.position[0] * 100}% ${source.position[1] * 100}%`, ...style}} />;
}

function ReelScene({scene}) {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 7], [0.96, 1], {extrapolateRight: 'clamp'});
  const caption = scene.captions.find(c => frame >= c.startFrame && frame < c.endFrame);
  const hasProof = Boolean(scene.proof);
  return <AbsoluteFill style={{fontFamily: font, color: 'white', background: '#191b20', overflow: 'hidden'}}>
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 30% 25%, #434550, #121317 75%)'}} />
    {scene.camera && <AbsoluteFill style={hasProof ? {filter: 'blur(22px) brightness(0.32)', transform: 'scale(1.08)'} : {}}>
      <SourceVideo source={scene.camera} />
    </AbsoluteFill>}
    <AbsoluteFill style={{background: 'linear-gradient(0deg, #050608e8 0%, transparent 48%, #05060860 100%)'}} />
    {scene.heading && <div style={{position: 'absolute', top: 148, left: 72, width: 936, textAlign: 'center'}}>
      <div style={{display: 'inline-block', maxWidth: '100%', padding: '18px 29px', background: yellow,
        color: '#171717', borderRadius: 18, transform: 'rotate(-2deg)', fontSize: 43,
        fontWeight: 900, lineHeight: 1.12, boxShadow: '0 7px 25px #0007', overflowWrap: 'anywhere'}}>
        {scene.heading.toUpperCase()}
      </div>
    </div>}
    {hasProof && <div style={{position: 'absolute', left: 55, top: 440, width: 970,
      height: 830, transform: `scale(${enter})`, borderRadius: 26, overflow: 'hidden',
      background: '#f4f3ee', boxShadow: '0 20px 70px #0009', border: '3px solid #ffffff70'}}>
      <div style={{height: 752, padding: 10}}>
        {scene.proof.kind === 'image'
          ? <Img src={staticFile(scene.proof.src)} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
          : <SourceVideo source={scene.proof} muted style={{objectFit: 'contain'}} />}
      </div>
      <div style={{height: 78, display: 'flex', alignItems: 'center', padding: '0 28px',
        background: '#23252b', color: '#e9e9ec', fontSize: 29, fontWeight: 700, lineHeight: 1.1}}>
        {scene.proof.label}
      </div>
    </div>}
    {caption && !scene.cta && <div style={{position: 'absolute', top: 1410, left: 60, width: 960,
      textAlign: 'center', fontSize: caption.text.length > 40 ? 70 : 88, lineHeight: 1.06,
      fontWeight: 900, textShadow: shadow, letterSpacing: -2, overflowWrap: 'anywhere'}}>
      {caption.text.split(/\s+/).map((word, i) => <React.Fragment key={i}>
        {i > 0 ? ' ' : ''}<span style={{color: caption.highlight.includes(word.replace(/[^\p{L}\p{N}]/gu, '').toLowerCase()) ? yellow : 'white'}}>{word.toUpperCase()}</span>
      </React.Fragment>)}
    </div>}
    {scene.cta && <div style={{position: 'absolute', top: 1240, left: 75, width: 930, textAlign: 'center'}}>
      {scene.cta.eyebrow && <div style={{fontSize: 59, fontWeight: 900, marginBottom: 20, textShadow: shadow}}>{scene.cta.eyebrow.toUpperCase()}</div>}
      <div style={{display: 'inline-block', background: yellow, color: '#111', padding: '20px 32px',
        fontWeight: 900, fontSize: scene.cta.text.length > 15 ? 83 : 112, lineHeight: 1,
        borderRadius: 20, transform: 'rotate(-2deg)', boxShadow: '0 12px 40px #0008'}}>{scene.cta.text.toUpperCase()}</div>
      {scene.cta.subtitle && <div style={{fontSize: 39, lineHeight: 1.15, fontWeight: 800,
        marginTop: 27, textShadow: shadow}}>{scene.cta.subtitle.toUpperCase()}</div>}
    </div>}
  </AbsoluteFill>;
}

export function VerticalProofReel({plan}) {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return <AbsoluteFill>
    {plan.scenes.map(scene => <Sequence key={scene.id} from={scene.fromFrame} durationInFrames={scene.durationInFrames}>
      <ReelScene scene={scene} />
    </Sequence>)}
    <div style={{position: 'absolute', left: 0, top: 0, width: '100%', height: 10, background: '#ffffff35'}} />
    <div style={{position: 'absolute', left: 0, top: 0, height: 10, background: yellow,
      width: `${100 * frame / Math.max(1, durationInFrames - 1)}%`}} />
  </AbsoluteFill>;
}

registerRoot(() => <Composition id="VerticalProofReel" component={VerticalProofReel}
  width={1080} height={1920} fps={30} durationInFrames={30}
  defaultProps={{plan: {fps: 30, durationInFrames: 30, scenes: []}}}
  calculateMetadata={({props}) => ({fps: props.plan.fps, durationInFrames: props.plan.durationInFrames})} />);
