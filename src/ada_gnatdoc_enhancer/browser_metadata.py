"""Optional browser qualification assertions; no Playwright runtime dependency."""


def assert_document_metadata(document, title, language='en'):
    """Wait for the destination document, then check all three metadata fields."""
    document.wait_for_function(
        "expected => document.readyState !== 'loading' && "
        "JSON.stringify([document.title, document.documentElement.lang, document.characterSet]) "
        "=== JSON.stringify(expected)", arg=[title, language, 'UTF-8'])


def assert_api_documents(page, titles, package_pages, package):
    """Reacquire the frame after every navigation; never retain a stale Frame."""
    from urllib.parse import urlsplit
    page.frame_locator('iframe').get_by_role('heading', name=package, exact=True).wait_for()
    frame = page.frame(name='document-content')
    expected = package_pages[package]
    frame.wait_for_url(lambda url: urlsplit(url).path.endswith('/' + expected))
    assert_document_metadata(page, titles['api/index.html'])
    assert_document_metadata(frame, titles[expected])


def native_frame_history(page, direction):
    """Native iframe history does not navigate the outer Page (especially without JS)."""
    if direction not in ('back', 'forward'):
        raise ValueError('unsupported history direction')
    frame = page.frame(name='document-content')
    with frame.expect_navigation(wait_until='load'):
        page.evaluate('history.' + direction + '()')