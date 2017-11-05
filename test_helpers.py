from datasite import app
import pytest
import json


@pytest.mark.parametrize('path,expected', [
    ('foo', ['foo']),
    ('foo,bar', ['foo', 'bar']),
    ('123,433,112', ['123', '433', '112']),
    ('123%2C433,112', ['123,433', '112']),
    ('123%2F433%2F112', ['123/433/112']),
])
def test_compound_pks_from_path(path, expected):
    assert expected == app.compound_pks_from_path(path)


@pytest.mark.parametrize('row,pks,expected_path', [
    ({'A': 'foo', 'B': 'bar'}, ['A', 'B'], 'foo,bar'),
    ({'A': 'f,o', 'B': 'bar'}, ['A', 'B'], 'f%2Co,bar'),
    ({'A': 123}, ['A'], '123'),
])
def test_path_from_row_pks(row, pks, expected_path):
    actual_path = app.path_from_row_pks(row, pks)
    assert expected_path == actual_path


@pytest.mark.parametrize('obj,expected', [
    ({
        'Description': 'Soft drinks',
        'Picture': b"\x15\x1c\x02\xc7\xad\x05\xfe",
        'CategoryID': 1,
    }, """
        {"CategoryID": 1, "Description": "Soft drinks", "Picture": {"$base64": true, "encoded": "FRwCx60F/g=="}}
    """.strip()),
])
def test_custom_json_encoder(obj, expected):
    actual = json.dumps(
        obj,
        cls=app.CustomJSONEncoder,
        sort_keys=True
    )
    assert expected == actual


@pytest.mark.parametrize('args,expected_where,expected_params', [
    (
        {
            'name_english__contains': ['foo'],
        },
        '"name_english" like ?',
        ['%foo%']
    ),
    (
        {
            'foo': ['bar'],
            'bar__contains': ['baz'],
        },
        '"bar" like ? and "foo" = ?',
        ['%baz%', 'bar']
    ),
    (
        {
            'foo__startswith': ['bar'],
            'bar__endswith': ['baz'],
        },
        '"bar" like ? and "foo" like ?',
        ['%baz', 'bar%']
    ),
    (
        {
            'foo__lt': ['1'],
            'bar__gt': ['2'],
            'baz__gte': ['3'],
            'bax__lte': ['4'],
        },
        '"bar" > ? and "bax" <= ? and "baz" >= ? and "foo" < ?',
        ['2', '4', '3', '1']
    ),
    (
        {
            'foo__like': ['2%2'],
            'zax__glob': ['3*'],
        },
        '"foo" like ? and "zax" glob ?',
        ['2%2', '3*']
    ),
])
def test_build_where(args, expected_where, expected_params):
    actual_where, actual_params = app.build_where_clause(args)
    assert expected_where == actual_where
    assert expected_params == actual_params


@pytest.mark.parametrize('bad_sql', [
    'update blah;',
    'PRAGMA case_sensitive_like = true'
    "SELECT * FROM pragma_index_info('idx52')",
])
def test_validate_sql_select_bad(bad_sql):
    with pytest.raises(app.InvalidSql):
        app.validate_sql_select(bad_sql)


@pytest.mark.parametrize('good_sql', [
    'select count(*) from airports',
    'select foo from bar',
    'select 1 + 1',
])
def test_validate_sql_select_good(good_sql):
    app.validate_sql_select(good_sql)
