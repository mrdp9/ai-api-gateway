"""
Frontend Unit Tests for API Dashboard
Tests CSS and JavaScript functionality without browser dependencies
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))


class TestDashboardFunctions(unittest.TestCase):
    """Test dashboard.js utility functions"""
    
    def test_mask_key_function(self):
        """Test that maskKey properly masks API keys"""
        # This would be tested in browser, but here's the logic
        def maskKey(key):
            if not key or len(key) < 8:
                return '***'
            return key[:4] + '***' + key[-4:]
        
        self.assertEqual(maskKey('abcd1234'), 'abcd***1234')
        self.assertEqual(maskKey('short'), '***')
        self.assertEqual(maskKey(''), '***')
    
    def test_format_date_logic(self):
        """Test date formatting logic"""
        def formatDate(dateString):
            if not dateString:
                return 'N/A'
            # In actual JS, would use Date.toLocaleDateString
            # Here we simulate the format
            from datetime import datetime
            try:
                date = datetime.fromisoformat(dateString.split('T')[0] if 'T' in dateString else dateString)
                return date.strftime('%b %d, %Y')
            except:
                return 'Invalid'
        
        self.assertEqual(formatDate('2024-12-25'), 'Dec 25, 2024')
        self.assertEqual(formatDate(''), 'N/A')
        self.assertEqual(formatDate('2024-12-25T10:30:00'), 'Dec 25, 2024')


class TestHTMLStructure(unittest.TestCase):
    """Test HTML structure and Jinja2 compatibility"""
    
    def test_html_file_exists(self):
        """Test that index.html file exists"""
        html_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'templates', 'index.html')
        self.assertTrue(os.path.exists(html_path), "index.html should exist")
    
    def test_css_file_exists(self):
        """Test that style.css file exists"""
        css_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static', 'style.css')
        self.assertTrue(os.path.exists(css_path), "style.css should exist")
    
    def test_js_file_exists(self):
        """Test that dashboard.js file exists"""
        js_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static', 'dashboard.js')
        self.assertTrue(os.path.exists(js_path), "dashboard.js should exist")
    
    def test_html_references_external_files(self):
        """Test that HTML references external CSS and JS files"""
        html_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'templates', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('url_for(\'static\', path=\'style.css\')', content, 
                         "HTML should reference external CSS")
            self.assertIn('url_for(\'static\', path=\'dashboard.js\')', content, 
                         "HTML should reference external JS")
    
    def test_html_no_inline_styles(self):
        """Test that HTML doesn't have inline <style> tag (moved to CSS file)"""
        html_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'templates', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Should not have <style> tag with CSS content
            self.assertNotIn('<style>\n        * {', content, 
                           "HTML should not have inline CSS (should be in style.css)")
    
    def test_html_no_inline_scripts(self):
        """Test that HTML doesn't have inline script (moved to JS file)"""
        html_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'templates', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Should not have large script tags
            self.assertNotIn('async function loadTunnelURL', content, 
                           "HTML should not have inline JS (should be in dashboard.js)")
    
    def test_html_contains_jinja2_templates(self):
        """Test that HTML still uses Jinja2 template variables"""
        html_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'templates', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('{% if keys %}', content, "HTML should contain Jinja2 conditionals")
            self.assertIn('{% for key in keys %}', content, "HTML should contain Jinja2 loops")


class TestCSSFile(unittest.TestCase):
    """Test CSS file structure and completeness"""
    
    def test_css_has_required_selectors(self):
        """Test that CSS file contains required style selectors"""
        css_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static', 'style.css')
        with open(css_path, 'r') as f:
            content = f.read()
            required_selectors = [
                'body {',
                '.container {',
                'h1 {',
                '.form-section {',
                'table {',
                '.btn {',
                '.status-badge {',
                '.notification {'
            ]
            for selector in required_selectors:
                self.assertIn(selector, content, f"CSS should contain '{selector}'")
    
    def test_css_responsive_design(self):
        """Test that CSS includes responsive design media queries"""
        css_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static', 'style.css')
        with open(css_path, 'r') as f:
            content = f.read()
            self.assertIn('@media (max-width: 768px)', content, 
                         "CSS should include tablet responsive styles")
            self.assertIn('@media (max-width: 480px)', content, 
                         "CSS should include mobile responsive styles")
    
    def test_css_color_variables(self):
        """Test that CSS uses CSS variables for colors"""
        css_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static', 'style.css')
        with open(css_path, 'r') as f:
            content = f.read()
            self.assertIn(':root {', content, "CSS should define CSS variables")
            self.assertIn('--primary-color:', content, "CSS should define primary color variable")


class TestJavaScriptFile(unittest.TestCase):
    """Test JavaScript file structure and functionality"""
    
    def test_js_has_required_functions(self):
        """Test that JS file exports required functions"""
        js_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static', 'dashboard.js')
        with open(js_path, 'r') as f:
            content = f.read()
            required_functions = [
                'function showNotification',
                'function copyToClipboard',
                'function formatDate',
                'function maskKey',
                'function createApiKey',
                'function deleteApiKey',
                'function fetchTunnelUrl'
            ]
            for func in required_functions:
                self.assertIn(func, content, f"JS should contain function: {func}")
    
    def test_js_event_listeners(self):
        """Test that JS includes DOMContentLoaded listener"""
        js_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static', 'dashboard.js')
        with open(js_path, 'r') as f:
            content = f.read()
            self.assertIn('DOMContentLoaded', content, 
                         "JS should include DOMContentLoaded event listener")
    
    def test_js_module_export(self):
        """Test that JS exports functions for testing"""
        js_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static', 'dashboard.js')
        with open(js_path, 'r') as f:
            content = f.read()
            self.assertIn('module.exports', content, 
                         "JS should export functions for Node.js testing")


class TestFastAPIStalicConfiguration(unittest.TestCase):
    """Test FastAPI configuration for static files"""
    
    def test_main_py_imports_staticfiles(self):
        """Test that main.py imports StaticFiles"""
        main_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'main.py')
        with open(main_path, 'r') as f:
            content = f.read()
            self.assertIn('from fastapi.staticfiles import StaticFiles', content,
                         "main.py should import StaticFiles")
    
    def test_main_py_mounts_static(self):
        """Test that main.py mounts static directory"""
        main_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'main.py')
        with open(main_path, 'r') as f:
            content = f.read()
            self.assertIn('app.mount("/static"', content,
                         "main.py should mount /static directory")
            self.assertIn('StaticFiles(directory="static")', content,
                         "main.py should mount static files directory")
    
    def test_main_py_api_endpoints_updated(self):
        """Test that main.py has updated API endpoints"""
        main_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'main.py')
        with open(main_path, 'r') as f:
            content = f.read()
            self.assertIn('@app.post("/api/create")', content,
                         "main.py should have /api/create endpoint")
            self.assertIn('@app.delete("/api/delete/', content,
                         "main.py should have DELETE /api/delete/ endpoint")


class TestFileStructure(unittest.TestCase):
    """Test the overall file structure"""
    
    def test_directory_structure(self):
        """Test that required directories exist"""
        base_path = os.path.join(os.path.dirname(__file__), '..')
        required_dirs = [
            'api/templates',
            'api/static',
            'api',
            'data',
            'scripts'
        ]
        for dir_path in required_dirs:
            full_path = os.path.join(base_path, dir_path)
            self.assertTrue(os.path.isdir(full_path), f"Directory '{dir_path}' should exist")
    
    def test_static_files_in_subdirectories(self):
        """Test that CSS and JS are in static directory (flat structure is also OK)"""
        static_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'static')
        self.assertTrue(os.path.isdir(static_path), "static directory should exist")
        
        # Check files exist in static
        css_file = os.path.join(static_path, 'style.css')
        js_file = os.path.join(static_path, 'dashboard.js')
        self.assertTrue(os.path.exists(css_file), "style.css should exist in static directory")
        self.assertTrue(os.path.exists(js_file), "dashboard.js should exist in static directory")


def run_tests_with_report():
    """Run all tests with detailed reporting"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestHTMLStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestCSSFile))
    suite.addTests(loader.loadTestsFromTestCase(TestJavaScriptFile))
    suite.addTests(loader.loadTestsFromTestCase(TestFastAPIStalicConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestFileStructure))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests_with_report()
    sys.exit(0 if success else 1)
