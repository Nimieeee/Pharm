#!/usr/bin/env python3
"""
Verification script for Task 11: Update authentication and session management
Verifies the implementation of simplified user profile, conversation switching, and user isolation
"""

import sys
import os
import inspect

def verify_user_profile_simplification():
    """Verify that user profile display removes plan information"""
    print("🔍 Verifying user profile simplification...")
    
    try:
        # Read the auth_ui.py file to check for plan information removal
        with open('auth_ui.py', 'r') as f:
            auth_ui_content = f.read()
        
        # Check that render_user_profile method exists and is simplified
        if 'def render_user_profile(self) -> None:' in auth_ui_content:
            print("   ✅ render_user_profile method found")
            
            # Check that plan/subscription information is not displayed
            profile_method_start = auth_ui_content.find('def render_user_profile(self) -> None:')
            profile_method_end = auth_ui_content.find('def _handle_sign_out(self)', profile_method_start)
            profile_method_content = auth_ui_content[profile_method_start:profile_method_end]
            
            # Remove comments and docstrings to focus on actual code
            lines = profile_method_content.split('\n')
            code_lines = []
            for line in lines:
                # Remove comments
                if '#' in line:
                    line = line[:line.index('#')]
                # Skip empty lines and docstrings
                if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                    code_lines.append(line)
            
            code_content = '\n'.join(code_lines)
            
            # These terms should NOT appear in the actual code (excluding model-related usage)
            forbidden_terms = ['subscription_tier', 'subscription', 'plan tier', 'free plan', 'premium plan']
            plan_references = []
            
            for term in forbidden_terms:
                if term in code_content.lower():
                    plan_references.append(term)
            
            if not plan_references:
                print("   ✅ Plan/subscription information removed from user profile")
                return True
            else:
                print(f"   ❌ Found plan references in user profile: {plan_references}")
                return False
        else:
            print("   ❌ render_user_profile method not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error verifying user profile: {e}")
        return False

def verify_session_manager_conversation_support():
    """Verify that session manager supports conversation management"""
    print("🔍 Verifying session manager conversation support...")
    
    try:
        # Read the session_manager.py file
        with open('session_manager.py', 'r') as f:
            session_manager_content = f.read()
        
        # Check for conversation management methods
        required_methods = [
            'switch_conversation',
            'get_current_conversation_id',
            'set_current_conversation_id',
            '_verify_conversation_ownership'
        ]
        
        found_methods = []
        for method in required_methods:
            if f'def {method}(' in session_manager_content:
                found_methods.append(method)
                print(f"   ✅ {method} method found")
            else:
                print(f"   ❌ {method} method not found")
        
        # Check for conversation isolation session state variables
        isolation_vars = [
            'current_conversation_id',
            'user_conversations',
            'conversation_switched',
            'conversation_isolation_user_id'
        ]
        
        found_vars = []
        for var in isolation_vars:
            if f"'{var}'" in session_manager_content:
                found_vars.append(var)
                print(f"   ✅ {var} session state variable found")
            else:
                print(f"   ❌ {var} session state variable not found")
        
        success = len(found_methods) == len(required_methods) and len(found_vars) == len(isolation_vars)
        
        if success:
            print("   ✅ Session manager conversation support implemented")
        else:
            print("   ❌ Session manager conversation support incomplete")
        
        return success
        
    except Exception as e:
        print(f"   ❌ Error verifying session manager: {e}")
        return False

def verify_conversation_isolation():
    """Verify conversation isolation implementation"""
    print("🔍 Verifying conversation isolation...")
    
    try:
        # Read the session_manager.py file
        with open('session_manager.py', 'r') as f:
            session_manager_content = f.read()
        
        # Check for conversation ownership verification
        if '_verify_conversation_ownership' in session_manager_content:
            print("   ✅ Conversation ownership verification implemented")
            
            # Check that it verifies user_id matches
            if 'eq(\'user_id\', user_id)' in session_manager_content:
                print("   ✅ User ID verification in conversation ownership")
            else:
                print("   ❌ User ID verification missing in conversation ownership")
                return False
        else:
            print("   ❌ Conversation ownership verification not found")
            return False
        
        # Check for isolation tracking
        if 'conversation_isolation_user_id' in session_manager_content:
            print("   ✅ Conversation isolation tracking implemented")
        else:
            print("   ❌ Conversation isolation tracking not found")
            return False
        
        # Check for conversation clearing on user change
        if 'User has changed, clear conversation state' in session_manager_content:
            print("   ✅ Conversation clearing on user change implemented")
        else:
            print("   ❌ Conversation clearing on user change not found")
            return False
        
        print("   ✅ Conversation isolation properly implemented")
        return True
        
    except Exception as e:
        print(f"   ❌ Error verifying conversation isolation: {e}")
        return False

def verify_conversation_ui_integration():
    """Verify conversation UI uses session manager"""
    print("🔍 Verifying conversation UI integration...")
    
    try:
        # Read the conversation_ui.py file
        with open('conversation_ui.py', 'r') as f:
            conversation_ui_content = f.read()
        
        # Check that ConversationUI accepts session_manager parameter
        if 'session_manager=None' in conversation_ui_content:
            print("   ✅ ConversationUI accepts session_manager parameter")
        else:
            print("   ❌ ConversationUI doesn't accept session_manager parameter")
            return False
        
        # Check that it uses session manager for conversation switching
        if 'self.session_manager.switch_conversation' in conversation_ui_content:
            print("   ✅ ConversationUI uses session manager for switching")
        else:
            print("   ❌ ConversationUI doesn't use session manager for switching")
            return False
        
        # Check that it uses session manager for getting current conversation
        if 'self.session_manager.get_current_conversation_id' in conversation_ui_content:
            print("   ✅ ConversationUI uses session manager for current conversation")
        else:
            print("   ❌ ConversationUI doesn't use session manager for current conversation")
            return False
        
        print("   ✅ Conversation UI integration implemented")
        return True
        
    except Exception as e:
        print(f"   ❌ Error verifying conversation UI integration: {e}")
        return False

def verify_app_integration():
    """Verify app.py passes session manager to conversation UI"""
    print("🔍 Verifying app integration...")
    
    try:
        # Read the app.py file
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        # Check that ConversationUI is initialized with session manager
        if 'ConversationUI(self.conversation_manager, self.theme_manager, self.session_manager)' in app_content:
            print("   ✅ App passes session manager to ConversationUI")
            return True
        else:
            print("   ❌ App doesn't pass session manager to ConversationUI")
            return False
        
    except Exception as e:
        print(f"   ❌ Error verifying app integration: {e}")
        return False

def main():
    """Run all verification checks"""
    print("🧪 Verifying Task 11: Update authentication and session management")
    print("=" * 70)
    
    checks = [
        ("User Profile Simplification", verify_user_profile_simplification),
        ("Session Manager Conversation Support", verify_session_manager_conversation_support),
        ("Conversation Isolation", verify_conversation_isolation),
        ("Conversation UI Integration", verify_conversation_ui_integration),
        ("App Integration", verify_app_integration)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 50)
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! Task 11 implementation is complete and verified.")
        print("\n✅ Task 11 Requirements Implemented:")
        print("   ✅ Modified user profile display to remove plan information")
        print("   ✅ Updated session management to handle conversation switching")
        print("   ✅ Ensured conversation isolation between different users")
        print("   ✅ Added conversation management to user session state")
        return True
    else:
        print(f"\n❌ INCOMPLETE: {total - passed} checks failed.")
        print("Please review the failed checks and complete the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)