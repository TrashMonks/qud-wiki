from qbe.helpers import displayname_to_wiki as dtw


def test_displayname_to_wiki():
    assert dtw('test') == 'test'
    assert dtw('{{y|raw beetle meat}}') == "{{Qud shader|y|raw beetle meat}}"
    assert dtw('{{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}') ==\
        '{{Qud shader|r|La}} {{Qud shader|text=Jeunesse|colors=r-R-R-W-W-w-w|type=sequence}}'
    assert dtw('{{K|{{crysteel|crysteel}} mace}}') ==\
        '{{Qud shader|crysteel|crysteel}}{{Qud shader|K| mace}}'
    assert dtw('{{O|persistent {{G-W-o sequence|papaya}}}}') ==\
        '{{Qud shader|O|persistent }}{{Qud shader|text=papaya|colors=G-W-o|type=sequence}}'
    # ignoring shimmering for now
    assert dtw('{{shimmering b-b-B sequence|xyloschemer}}') ==\
        '{{Qud shader|text=xyloschemer|colors=b-b-B|type=sequence}}'
