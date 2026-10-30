"""Advisory-only NVIDIA Nemotron / Nebius Token Factory wrapper.

No hardware access, no commands, no auto-generated dosing setpoints.
When key is absent or API fails, explicitly reports offline fallback.
"""
import json
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
except ImportError:
    pass  # Environment-only configuration still works without python-dotenv.
from .analytics import summary, offline_explanation

DEFAULT_BASE='https://api.tokenfactory.nebius.com/v1'
DEFAULT_MODEL='nvidia/nemotron-3-super-120b-a12b'
SYSTEM_PROMPT='''You are DewaterIQ, a SYNTHETIC industrial process telemetry reviewer.
All input observations are from a toy simulation, NOT real drilling equipment and
NOT validated industrial limits. Your task: summarize observations, make cautious
hypotheses, distinguish a deliberate volume-loss mode from equipment faults, and
suggest only non-operational operator CHECKS and data/field-validation next steps.
Never give a numeric control setpoint, chemical dosing instruction, command, PLC/VFD
code, equipment control action, hazardous intervention or safety override. Never
claim the simulation predicts real equipment or that its outputs are safe for use.
Provide: (1) measurements (2) likely but UNVERIFIED interpretations (3) checks
(4) data gaps. Keep within 230 words. State 'SIMULATION / ADVISORY ONLY'.'''


def analyze(records, similar=None, force_offline=False):
    s=summary(records)
    if not s: return {'status':'empty','model':None,'text':'No telemetry.'}
    similar=similar or []
    key=os.getenv('NEBIUS_API_KEY') or os.getenv('NEBIUS_TOKEN_FACTORY_KEY')
    offline=offline_explanation(records, similar)
    if force_offline or not key:
        return {'status':'offline','model':None,'text':offline,
                'note':'Nebius was not called; set NEBIUS_API_KEY for live NVIDIA inference.'}
    try:
        from openai import OpenAI
        url=os.environ.get('NEBIUS_BASE_URL',DEFAULT_BASE)
        model=os.environ.get('NEBIUS_MODEL',DEFAULT_MODEL)
        client=OpenAI(api_key=key,base_url=url,timeout=25.0,max_retries=0)
        payload={'summary':s,
                 'recent_samples':records[-5:],
                 'similar_synthetic_runs':similar,
                 'metadata':{'all_data':'synthetic','automation':'none','safety':'advisory_only'}}
        completion=client.chat.completions.create(
            model=model,
            messages=[{'role':'system','content':SYSTEM_PROMPT},
                      {'role':'user','content':json.dumps(payload,allow_nan=False)}],
            temperature=0.15,max_tokens=550)
        content=completion.choices[0].message.content or ''
        if not content.strip(): raise RuntimeError('Empty response')
        return {'status':'live_nebius','model':model,
                'text':'SIMULATION / ADVISORY ONLY\n'+content.strip(),
                'note':'NVIDIA model called through Nebius Token Factory; no equipment controls exposed.'}
    except Exception as exc:
        # Avoid exposing API key or full HTTP exception body to UI/logs.
        return {'status':'offline_api_unavailable','model':None,'text':offline,
                'note':f'Live Nebius call unavailable ({type(exc).__name__}); showing offline rules only.'}
