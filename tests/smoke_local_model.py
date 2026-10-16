"""Real local inference on synthetic data, never assignment evidence."""
import json

from lib.model_provider import ask
from lib.stage_runtime import run_directory, run_stage


def main(metrics):
    metrics['input_count'] = 1
    result = ask('local_smoke', run_directory(), {'mode': 'example'},
                 'This is a synthetic connection test, not source evidence.',
                 'Return status ok and sum 5 for 2 + 3.', {'example': True, 'a': 2, 'b': 3},
                 {'type': 'object', 'properties': {'status': {'type': 'string', 'enum': ['ok']},
                  'sum': {'type': 'integer'}}, 'required': ['status', 'sum'],
                  'additionalProperties': False}, metrics)
    if result != {'status': 'ok', 'sum': 5}:
        raise ValueError('Local inference smoke test failed')
    metrics['output_count'] = 1
    print(json.dumps({'example': True, **result}))


if __name__ == '__main__':
    raise SystemExit(run_stage(main))
