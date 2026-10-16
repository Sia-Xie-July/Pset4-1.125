"""Publish a validated three-file bundle without discarding earlier drafts."""
import os
import tempfile
from pathlib import Path


def publish(run, folder, documents, briefs, evidence, metadata):
    index = {brief['piece_id']:brief for brief in briefs}
    with tempfile.TemporaryDirectory(prefix='.'+folder+'-',dir=run) as temporary:
        staged = Path(temporary)/folder
        staged.mkdir()
        for document in documents:
            label = 'EXAMPLE/REPLAY OUTPUT — not publication evidence.\n\n' if metadata.get('mode') in ('example','replay') else ''
            text = label+document['markdown'].rstrip()+'\n\nAs of: '+metadata['as_of_date']+' (UTC).\n\n'
            text += evidence.source_notes(index[document['piece_id']])
            (staged/(document['piece_id']+'.md')).write_text(text,encoding='utf-8')
        target = run/folder
        if target.exists():
            archived = run/'attempts'/os.environ['INVOCATION_ID']
            archived.mkdir(parents=True,exist_ok=True)
            target.rename(archived/folder)
        staged.rename(target)
    return [{'piece_id':doc['piece_id'],'path':(run/folder/(doc['piece_id']+'.md')).relative_to(Path.cwd()).as_posix(),
             'claim_ids':doc['claim_ids']} for doc in sorted(documents,key=lambda d:d['piece_id'])]
