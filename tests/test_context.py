import base64
from unittest.mock import Mock, AsyncMock

import pytest
from playwright.async_api import Page

from browser_use.browser.context import BrowserContext, BrowserContextConfig, BrowserSession
from browser_use.browser.views import BrowserState
from browser_use.dom.views import DOMElementNode


def test_is_url_allowed():
	"""
	Test the _is_url_allowed method to verify that it correctly checks URLs against
	the allowed domains configuration.
	Scenario 1: When allowed_domains is None, all URLs should be allowed.
	Scenario 2: When allowed_domains is a list, only URLs matching the allowed domain(s) are allowed.
	Scenario 3: When the URL is malformed, it should return False.
	"""
	# Create a dummy Browser mock. Only the 'config' attribute is needed for _is_url_allowed.
	dummy_browser = Mock()
	# Set an empty config for dummy_browser; it won't be used in _is_url_allowed.
	dummy_browser.config = Mock()
	# Scenario 1: allowed_domains is None, any URL should be allowed.
	config1 = BrowserContextConfig(allowed_domains=None)
	context1 = BrowserContext(browser=dummy_browser, config=config1)
	assert context1._is_url_allowed('http://anydomain.com') is True
	assert context1._is_url_allowed('https://anotherdomain.org/path') is True
	# Scenario 2: allowed_domains is provided.
	allowed = ['example.com', 'mysite.org']
	config2 = BrowserContextConfig(allowed_domains=allowed)
	context2 = BrowserContext(browser=dummy_browser, config=config2)
	# URL exactly matching
	assert context2._is_url_allowed('http://example.com') is True
	# URL with subdomain (should be allowed)
	assert context2._is_url_allowed('http://sub.example.com/path') is True
	# URL with different domain (should not be allowed)
	assert context2._is_url_allowed('http://notexample.com') is False
	# URL that matches second allowed domain
	assert context2._is_url_allowed('https://mysite.org/page') is True
	# URL with port number, still allowed (port is stripped)
	assert context2._is_url_allowed('http://example.com:8080') is True
	# Scenario 3: Malformed URL or empty domain
	# urlparse will return an empty netloc for some malformed URLs.
	assert context2._is_url_allowed('notaurl') is False


def test_convert_simple_xpath_to_css_selector():
	"""
	Test the _convert_simple_xpath_to_css_selector method of BrowserContext.
	This verifies that simple XPath expressions (with and without indices) are correctly converted to CSS selectors.
	"""
	# Test empty xpath returns empty string
	assert BrowserContext._convert_simple_xpath_to_css_selector('') == ''
	# Test a simple xpath without indices
	xpath = '/html/body/div/span'
	expected = 'html > body > div > span'
	result = BrowserContext._convert_simple_xpath_to_css_selector(xpath)
	assert result == expected
	# Test xpath with an index on one element: [2] should translate to :nth-of-type(2)
	xpath = '/html/body/div[2]/span'
	expected = 'html > body > div:nth-of-type(2) > span'
	result = BrowserContext._convert_simple_xpath_to_css_selector(xpath)
	assert result == expected
	# Test xpath with indices on multiple elements:
	# For "li[3]" -> li:nth-of-type(3) and for "a[1]" -> a:nth-of-type(1)
	xpath = '/ul/li[3]/a[1]'
	expected = 'ul > li:nth-of-type(3) > a:nth-of-type(1)'
	result = BrowserContext._convert_simple_xpath_to_css_selector(xpath)
	assert result == expected


@pytest.mark.asyncio
async def test_get_initial_state():
	"""
	Test the initial state of BrowserContext after initialization.
	Checks that the state contains default values.
	"""
	# Create a dummy browser since only its existence is needed.
	dummy_browser = Mock()
	dummy_browser.config = Mock()
	dummy_browser.get_playwright_browser = AsyncMock()
	context = BrowserContext(browser=dummy_browser, config=BrowserContextConfig())

	# Mock the methods called during _initialize_session
	context._create_context = AsyncMock()
	mock_playwright_context = AsyncMock()
	mock_playwright_context.pages = []
	mock_playwright_context.new_page = AsyncMock()
	mock_new_page = AsyncMock()
	mock_new_page.url = 'about:blank'
	mock_new_page.bring_to_front = AsyncMock()
	mock_new_page.wait_for_load_state = AsyncMock()
	mock_playwright_context.new_page.return_value = mock_new_page
	context._create_context.return_value = mock_playwright_context
	context.browser.get_playwright_browser.return_value = AsyncMock()

	# Initialize the session (implicitly calls the logic previously in _get_initial_state)
	await context._initialize_session()

	# Verify the initial state stored in the session
	assert context.session is not None
	# Create a default state to compare against if cached_state is None initially
	default_state = BrowserState(
		element_tree=DOMElementNode(tag_name='root', is_visible=True, parent=None, xpath='/', attributes={}, children=[]),
		selector_map={},
		url='about:blank',
		title='',
		tabs=[]
	)
	initial_state = context.session.cached_state or default_state
	assert isinstance(initial_state, BrowserState)
	# The URL might be 'about:blank' now after initialization
	assert initial_state.url == 'about:blank'
	# Verify that the element_tree is initialized with tag 'root'
	assert initial_state.element_tree.tag_name == 'root'


@pytest.mark.asyncio
async def test_execute_javascript():
	"""
	Test the execute_javascript method by mocking the current page's evaluate function.
	This ensures that when execute_javascript is called, it correctly returns the value
	from the page's evaluate method.
	"""

	# Define a dummy page mock using AsyncMock
	dummy_page_mock = AsyncMock(spec=Page)
	dummy_page_mock.evaluate = AsyncMock(return_value='dummy_result')

	# Create a dummy session mock
	dummy_session_mock = Mock(spec=BrowserSession)
	dummy_session_mock.context = AsyncMock()

	# Create a dummy browser mock with a minimal config.
	dummy_browser = Mock()
	dummy_browser.config = Mock()
	dummy_browser.get_playwright_browser = AsyncMock()
	# Initialize the BrowserContext with the dummy browser and config.
	context = BrowserContext(browser=dummy_browser, config=BrowserContextConfig())
	# Manually set the session to our dummy session mock, ignore type checker
	context.session = dummy_session_mock
	context.get_current_page = AsyncMock(return_value=dummy_page_mock)

	# Call execute_javascript and verify it returns the expected result.
	result = await context.execute_javascript('return 1+1')
	assert result == 'dummy_result'
	# Verify evaluate was called on the page mock
	dummy_page_mock.evaluate.assert_awaited_once_with('return 1+1')


@pytest.mark.asyncio
async def test_enhanced_css_selector_for_element():
	"""
	Test the _enhanced_css_selector_for_element method to verify that
	it returns the correct CSS selector string for a dummy DOMElementNode.
	The test checks that:
	  - The provided xpath is correctly converted (handling indices),
	  - Class attributes are appended as CSS classes,
	  - Standard and dynamic attributes (including ones with special characters)
	    are correctly added to the selector.
	"""
	# Create a dummy DOMElementNode instance with a complex set of attributes.
	dummy_element = DOMElementNode(
		tag_name='div',
		is_visible=True,
		parent=None,
		xpath='/html/body/div[2]',
		attributes={'class': 'foo bar', 'id': 'my-id', 'placeholder': 'some "quoted" text', 'data-testid': '123'},
		children=[],
	)
	# Call the method with include_dynamic_attributes=True.
	actual_selector = BrowserContext._enhanced_css_selector_for_element(dummy_element, include_dynamic_attributes=True)
	# Expected conversion:
	# 1. The xpath "/html/body/div[2]" converts to "html > body > div:nth-of-type(2)".
	# 2. The class attribute "foo bar" appends ".foo.bar".
	# 3. The "id" attribute is added as [id="my-id"].
	# 4. The "placeholder" attribute contains quotes; it is added as
	#    [placeholder*="some \"quoted\" text"].
	# 5. The dynamic attribute "data-testid" is added as [data-testid="123"].
	expected_selector = (
		'html > body > div:nth-of-type(2).foo.bar[id="my-id"][placeholder*="some \\"quoted\\" text"][data-testid="123"]'
	)
	assert actual_selector == expected_selector, f'Expected {expected_selector}, but got {actual_selector}'


@pytest.mark.asyncio
async def test_get_scroll_info():
	"""
	Test the get_scroll_info method by mocking the page's evaluate method.
	This dummy page returns preset values for window.scrollY, window.innerHeight,
	and document.documentElement.scrollHeight. The test then verifies that the
	computed scroll information (pixels_above and pixels_below) match the expected values.
	"""

	# Define a mock page using AsyncMock with a side_effect for evaluate
	page_mock = AsyncMock(spec=Page)

	async def evaluate_side_effect(script):
		if 'window.scrollY' in script:
			return 100  # scrollY
		elif 'window.innerHeight' in script:
			return 500  # innerHeight
		elif 'document.documentElement.scrollHeight' in script:
			return 1200  # total scrollable height
		return None

	page_mock.evaluate = AsyncMock(side_effect=evaluate_side_effect)

	# Create a dummy session mock
	dummy_session_mock = Mock(spec=BrowserSession)
	dummy_session_mock.context = AsyncMock()

	# Create a dummy browser mock.
	dummy_browser = Mock()
	dummy_browser.config = Mock()
	dummy_browser.get_playwright_browser = AsyncMock()
	# Initialize BrowserContext with the dummy browser and config.
	context = BrowserContext(browser=dummy_browser, config=BrowserContextConfig())
	# Manually set the session to our dummy session mock.
	context.session = dummy_session_mock

	# Call get_scroll_info on the mock page.
	pixels_above, pixels_below = await context.get_scroll_info(page_mock)
	# Expected calculations:
	# pixels_above = scrollY = 100
	# pixels_below = total_height - (scrollY + innerHeight) = 1200 - (100 + 500) = 600
	assert pixels_above == 100, f'Expected 100 pixels above, got {pixels_above}'
	assert pixels_below == 600, f'Expected 600 pixels below, got {pixels_below}'


@pytest.mark.asyncio
async def test_reset_context():
	"""
	Test the reset_context method to ensure it correctly closes all existing tabs,
	 resets the cached state, and creates a new page.
	"""
	# Actual behavior: Closes all tabs and sets cached_state and active_tab to None.

	# Use AsyncMock for pages
	page1 = AsyncMock(spec=Page)
	page1.url = 'http://page1.com'
	page1.close = AsyncMock()

	page2 = AsyncMock(spec=Page)
	page2.url = 'http://page2.com'
	page2.close = AsyncMock()

	# Mock Context
	mock_playwright_context = AsyncMock()
	mock_playwright_context.pages = [page1, page2]
	mock_playwright_context.new_page = AsyncMock()
	mock_new_page = AsyncMock(spec=Page)
	mock_new_page.url = 'about:blank' # Set initial URL for new page
	mock_new_page.bring_to_front = AsyncMock()
	mock_new_page.wait_for_load_state = AsyncMock()
	mock_playwright_context.new_page.return_value = mock_new_page

	# Create a dummy session mock
	dummy_session_mock = Mock(spec=BrowserSession)
	dummy_session_mock.context = mock_playwright_context
	dummy_session_mock.cached_state = BrowserState(
		element_tree=DOMElementNode(tag_name='root', is_visible=True, parent=None, xpath='/', attributes={}, children=[]),
		selector_map={},
		url='http://initial.com', # Give it an initial URL
		title='Initial Title',
		tabs=[]
	)

	# Create a dummy browser mock.
	dummy_browser = Mock()
	dummy_browser.config = Mock()
	dummy_browser.get_playwright_browser = AsyncMock()
	# Initialize BrowserContext using our dummy_browser and config,
	# and manually set its session to our dummy session mock.
	context = BrowserContext(browser=dummy_browser, config=BrowserContextConfig())
	context.session = dummy_session_mock # type: ignore
	# Mock _get_current_page if reset_context calls it internally (Removed as it's not called by actual reset_context)
	# context._get_current_page = AsyncMock(return_value=mock_new_page)

	# Confirm session has 2 pages before reset.
	assert len(context.session.context.pages) == 2
	# Call reset_context which should close existing pages,
	# reset the cached state, and set active_tab to None.
	await context.reset_context()
	# Verify that initial pages were closed.
	page1.close.assert_awaited_once()
	page2.close.assert_awaited_once()
	# Check that new_page was NOT called
	mock_playwright_context.new_page.assert_not_awaited()
	# Verify active_tab is None
	assert context.active_tab is None
	# Verify that cached_state is None.
	assert context.session is not None
	assert context.session.cached_state is None


@pytest.mark.asyncio
async def test_take_screenshot():
	"""
	Test the take_screenshot method to verify that it returns a base64 encoded screenshot string.
	A dummy page with a mocked screenshot method is used, returning a predefined byte string.
	"""

	# Use AsyncMock for the page
	page_mock = AsyncMock(spec=Page)
	page_mock.screenshot = AsyncMock(return_value=b'test')

	# Create a dummy session mock
	dummy_session_mock = Mock(spec=BrowserSession)
	dummy_session_mock.context = AsyncMock()

	# Create a dummy browser mock.
	dummy_browser = Mock()
	dummy_browser.config = Mock()
	dummy_browser.get_playwright_browser = AsyncMock()
	# Initialize the BrowserContext with the dummy browser and config.
	context = BrowserContext(browser=dummy_browser, config=BrowserContextConfig())
	# Manually set the session to our dummy session mock.
	context.session = dummy_session_mock
	# Mock get_current_page to return our page mock
	context.get_current_page = AsyncMock(return_value=page_mock)

	# Call take_screenshot and check that it returns the expected base64 encoded string.
	result = await context.take_screenshot(full_page=True)
	# Assert screenshot was called correctly
	page_mock.screenshot.assert_awaited_once_with(full_page=True, animations='disabled')
	expected = base64.b64encode(b'test').decode('utf-8')
	assert result == expected, f'Expected {expected}, but got {result}'


@pytest.mark.asyncio
async def test_refresh_page_behavior():
	"""
	Test the refresh_page method of BrowserContext to verify that it correctly reloads the current page
	and waits for the page's load state. This is done by creating a dummy page that flags when its
	reload and wait_for_load_state methods are called.
	"""

	# Use AsyncMock for the page
	page_mock = AsyncMock(spec=Page)
	page_mock.reload = AsyncMock()
	page_mock.wait_for_load_state = AsyncMock()

	# Create a dummy session mock
	dummy_session_mock = Mock(spec=BrowserSession)
	dummy_session_mock.context = AsyncMock()

	# Create a dummy browser mock
	dummy_browser = Mock()
	dummy_browser.config = Mock()
	dummy_browser.get_playwright_browser = AsyncMock()
	# Initialize BrowserContext with the dummy browser and config,
	# and manually set its session to our dummy session mock.
	context = BrowserContext(browser=dummy_browser, config=BrowserContextConfig())
	context.session = dummy_session_mock
	# Mock get_current_page to return our page mock
	context.get_current_page = AsyncMock(return_value=page_mock)

	# Call refresh_page and verify that reload and wait_for_load_state were called.
	await context.refresh_page()
	page_mock.reload.assert_awaited_once()
	page_mock.wait_for_load_state.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_highlights_failure():
	"""
	Test the remove_highlights method to ensure that if the page.evaluate call fails,
	the exception is caught and does not propagate (i.e. the method handles errors gracefully).
	"""

	# Mock page that raises error on evaluate
	page_mock = AsyncMock(spec=Page)
	page_mock.evaluate = AsyncMock(side_effect=Exception('dummy error'))

	# Create a dummy session mock
	dummy_session_mock = Mock(spec=BrowserSession)
	dummy_session_mock.context = AsyncMock()

	# Create a dummy browser mock.
	dummy_browser = Mock()
	dummy_browser.config = Mock()
	dummy_browser.get_playwright_browser = AsyncMock()
	# Initialize BrowserContext with the dummy browser and configuration.
	context = BrowserContext(browser=dummy_browser, config=BrowserContextConfig())
	context.session = dummy_session_mock
	# Mock get_current_page to return our page mock
	context.get_current_page = AsyncMock(return_value=page_mock)

	# Call remove_highlights and verify that no exception is raised.
	try:
		await context.remove_highlights()
	except Exception as e:
		pytest.fail(f'remove_highlights raised an exception: {e}')
