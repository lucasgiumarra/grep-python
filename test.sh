#!/bin/bash

# This script is a local version of the CI pipeline defined in the .yml file.
# It runs a series of tests by executing the same shell commands.

# Exit immediately if a command exits with a non-zero status.
# The tests that are expected to fail will use `set +e` and `set -e`
set -e

echo "--- Running Local Tests ---"

# --- Run test 1: Match literal character ---
echo "Match literal character"
echo -n "apple" | python3 app/main.py -E "a"
echo -n "apple" | python3 app/ast.py -E "a"
echo "Test 1 passed."
echo ""

# --- Run test 2: Match digits ---
echo "Match digits"
echo -n "apple123" | python3 app/main.py -E "\d"
echo -n "apple123" | python3 app/ast.py -E "\d"
echo "Test 2 passed."
echo ""

# --- Run test 3: Match alphanumeric characters ---
echo "Match alphanumeric characters"
echo -n "alpha-num3ric" | python3 app/main.py -E "\w"
echo -n "alpha-num3ric" | python3 app/ast.py -E "\w"
echo "Test 3 passed."
echo ""

# --- Run test 4: Positive character groups ---
echo "Positive character groups"
echo -n "apple" | python3 app/main.py -E "[abc]"
echo -n "apple" | python3 app/ast.py -E "[abc]"
echo "Test 4 passed."
echo ""

# --- Run test 5: Negative character groups ---
echo "Negative character groups"
echo -n "apple" | python3 app/main.py -E "[^abc]"
echo -n "apple" | python3 app/main.py -E "[^bcd]"
echo -n "apple" | python3 app/ast.py -E "[^abc]"
echo -n "apple" | python3 app/ast.py -E "[^bcd]"
echo "Test 5 passed."
echo ""

# --- Run test 6: Combining character groups ---
echo "Combining character groups"
echo -n "1 apple" | python3 app/main.py -E "\d apple"
echo -n "1 apple" | python3 app/ast.py -E "\d apple"
echo "Test 6 passed."
echo ""

# --- Run test 7: Start of string anchor ---
echo "Start of string anchor"
set +e  # Allow commands to fail without exiting
echo -n "log" | python3 app/main.py -E "^log"
code1=$? # $? holds the exit code of the last command that was run
echo -n "slog" | python3 app/main.py -E "^log"
code2=$?
set -e  # Re-enable exit on error

if [ $code1 -ne 0 ]; then
  echo "Expected exit code 0 for 'log', got $code1"
  exit 1
fi

if [ $code2 -ne 1 ]; then
  echo "Expected exit code 1 for 'slog', got $code2"
  exit 1
fi
echo "Test 7 passed: correct exit codes received."
echo ""

# --- Run test 8: End of string anchor ---
echo "End of string anchor"
set +e  # Allow commands to fail without exiting
echo -n "dog" | python3 app/main.py -E "dog$"
code1=$? # $? holds the exit code of the last command that was run
echo -n "dogs" | python3 app/main.py -E "dog$"
code2=$?
set -e  # Re-enable exit on error

if [ $code1 -ne 0 ]; then
  echo "Expected exit code 0 for 'dog', got $code1"
  exit 1
fi

if [ $code2 -ne 1 ]; then
  echo "Expected exit code 1 for 'dogs', got $code2"
  exit 1
fi
echo "Test 8 passed: correct exit codes received."
echo ""

# --- Run test 9: Match one or more times ---
echo "Match one or more times"
set +e  # Allow commands to fail without exiting
echo -n "caats" | python3 app/main.py -E "ca+ts"
code1=$?
echo -n "ca" | python3 app/main.py -E "ca+t"
code2=$?
echo -n "ca" | python3 app/ast.py -E "ca+t"
code3=$?
echo -n "caats" | python3 app/ast.py -E "ca+ts"
code4=$?
echo -n "caaats" | python3 app/ast.py -E "ca+at"
code5=$?
set -e

if [ $code1 -ne 0 ]; then
  echo "Expected exit code 0 for 'caats', got $code1"
  exit 1
fi

if [ $code2 -ne 1 ]; then
  echo "Expected exit code 1 for 'ca', got $code2"
  exit 1
fi

if [ $code3 -ne 1 ]; then
  echo "Expected exit code 1 for 'ca', got $code3"
  exit 1
fi

if [ $code4 -ne 0 ]; then
  echo "Expected exit code 0 for 'caats', got $code4"
  exit 1
fi

if [ $code5 -ne 0 ]; then
  echo "Expected exit code 0 for 'caaats', got $code5"
  exit 1
fi
echo "Test 9 passed: correct exit codes received."
echo ""

# --- Run test 10: Match zero or more times ---
echo -e "\033[1m -- Match zero or more times -- \033[0m"
set +e  # Allow commands to fail without exiting
echo -n "cat" | python3 app/main.py -E "ca?t"
code1=$?
echo -n "act" | python3 app/main.py -E "ca?t"
code2=$?
echo -n "dog" | python3 app/main.py -E "ca?t"
code3=$?
echo -n "cat" | python3 app/ast.py -E "ca?t"
code4=$?
echo -n "act" | python3 app/ast.py -E "ca?t"
code5=$?
echo -n "dog" | python3 app/ast.py -E "ca?t"
code6=$?
set -e
if [ $code1 -ne 0 ]; then
  echo "Expected exit code 0 for 'cat', got $code1"
  exit 1
fi

if [ $code2 -ne 0 ]; then
  echo "Expected exit code 0 for 'act', got $code2"
  exit 1
fi

if [ $code3 -ne 1 ]; then
  echo "Expected exit code 1 for 'dog', got $code3"
  exit 1
fi

if [ $code4 -ne 0 ]; then
  echo "Expected exit code 0 for 'cat', got $code4"
  exit 1
fi

if [ $code5 -ne 0 ]; then
  echo "Expected exit code 0 for 'act', got $code5"
  exit 1
fi

if [ $code6 -ne 1 ]; then
  echo "Expected exit code 1 for 'dog', got $code6"
  exit 1
fi
echo "Test 10 passed: correct exit codes received."
echo ""

# --- Run test 11: Wildcard ---
echo "Wildcard"
set +e  # Allow commands to fail without exiting
echo -n "dog" | python3 app/main.py -E "d.g"
code1=$?
echo -n "dog" | python3 app/main.py -E "c.g"
code2=$?
echo -n "dog" | python3 app/ast.py -E "d.g"
code3=$?
echo -n "dog" | python3 app/ast.py -E "c.g"
code4=$?
set -e

if [ $code1 -ne 0 ]; then
  echo "Expected exit code 0 for 'dog', got $code1"
  exit 1
fi

if [ $code2 -ne 1 ]; then
  echo "Expected exit code 1 for 'dog', got $code2"
  exit 1
fi

if [ $code3 -ne 0 ]; then
  echo "Expected exit code 0 for 'dog', got $code3"
  exit 1
fi

if [ $code4 -ne 1 ]; then
  echo "Expected exit code 1 for 'dog', got $code4"
  exit 1
fi
echo "Test 11 passed."
echo ""

# --- Run test 12: Alternation ---
echo -e "\033[1m -- Alternation -- \033[0m"
set +e  # Allow commands to fail without exiting
echo -n "cat" | python3 app/ast.py -E "(cat|dog)"
code1=$?
echo -n "dog" | python3 app/ast.py -E "(cat|dog)"
code2=$?
set -e

if [ $code1 -ne 0 ]; then
  echo "Expected exit code 0 for 'cat', got $code1"
  exit 1
fi

if [ $code2 -ne 0 ]; then
  echo "Expected exit code 0 for 'dog', got $code2"
  exit 1
fi
echo "Test 12 passed."
echo ""


# --- Run test 13: Single Backreference ---
echo -e "\033[1m -- Single Backreference -- \033[0m"
set +e  # Allow commands to fail without exiting
echo -n "cat and cat" | python3 app/ast.py -E "(cat) and \1" 
code1=$?
echo -n "cat and dog" | python3 app/ast.py -E "(cat) and \1"
code2=$?
echo -n "cat and cat" | python3 app/ast.py -E "(\w+) and \1"
code3=$?
set -e

if [ $code1 -ne 0 ]; then
  echo "Expected exit code 0 for 'cat and cat', got $code1"
  exit 0
else 
  echo "test passed for cat and cat with ... (cat) and \1"
fi

if [ $code2 -ne 1 ]; then
  echo "Expected exit code 1 for 'cat and dog', got $code2"
  exit 1
else 
  echo "test passed for cat and dog with ... (cat) and \1"
fi

if [ $code3 -ne 0 ]; then
  echo "Expected exit code 0 for 'cat and cat' with (\w+) and \1, got $code3"
  exit 1
else 
  echo "test passed for cat and cat with ... (\w+) and \1"
fi

echo "Test 13 passed."
echo ""

echo "All tests passed successfully!"
echo ""