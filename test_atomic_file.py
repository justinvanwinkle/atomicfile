from __future__ import unicode_literals

from atomicfile import AtomicFile
import os


def test_file_creation(tmpdir):
    fn = str(tmpdir.join('test'))
    f = AtomicFile(fn)
    f.write('this is a test')
    f.close()

    with open(fn) as f:
        assert f.read() == 'this is a test'


def test_file_moved_only_after_close(tmpdir):
    fn = str(tmpdir.join('test'))
    f = AtomicFile(fn)
    f.write('this is a test')

    assert os.path.exists(fn) == False
    f.close()
    assert os.path.exists(fn)


def test_tmp_file_created_in_same_dir(tmpdir):
    fn = str(tmpdir.join('blkajdf'))
    assert len(tmpdir.listdir()) == 0

    f = AtomicFile(fn)
    f.write('nothing')

    assert len(tmpdir.listdir())
    assert tmpdir.listdir()[0].fnmatch('.blkajdf*')
    f.close()


def test_file_copied(tmpdir):
    tmpdir.join('old_file').write('contents here')

    f = AtomicFile(tmpdir.join('old_file').strpath)
    assert f.read() == 'contents here'
    f.close()


def test_file_not_copied(tmpdir):
    tmpdir.join('old_file').write('contents here')

    f = AtomicFile(tmpdir.join('old_file').strpath,
                   copy_existing=False)
    assert f.read() == ''
    f.close()


def test_abort(tmpdir):
    fn = str(tmpdir.join('test'))

    f = AtomicFile(fn)
    f.write('test')
    f.abort()
    assert len(tmpdir.listdir()) == 0

    f = AtomicFile(fn)
    f.write('test')
    del f

    assert len(tmpdir.listdir()) == 0

    tmpdir.join('test').write('test file is this')

    f = AtomicFile(fn)
    f.write('this is something else')
    f.abort()

    assert tmpdir.join('test').read() == 'test file is this'

    f = AtomicFile(fn)
    f.write('this is something else')
    del f

    assert tmpdir.join('test').read() == 'test file is this'


def test_context_success(tmpdir):
    tf = tmpdir.join('test')

    with AtomicFile(tf.strpath) as af:
        af.write('test data')

    assert tf.read() == 'test data'


def test_context_failure(tmpdir):
    tf = tmpdir.join('test')

    try:
        with AtomicFile(tf.strpath) as af:
            af.write('test data')
            raise Exception('blah blah')
    except Exception, e:
        assert e.message == 'blah blah'

    assert len(tmpdir.listdir()) == 0
