Feature: Web login
  Scenario: Valid credentials open the customer home
    Given the login page is open
    When the customer signs in with valid credentials
    Then the user shell is visible

  Scenario: Invalid credentials stay on the login view
    Given the login page is open
    When the customer signs in with invalid credentials
    Then the login view shows the credentials error without leaving

  Scenario: A network failure stays on the login view
    Given the login page is open
    When the customer signs in while the network is down
    Then the login view shows the network error without leaving

  Scenario: A visitor without session lands on login
    Given the portal is open
    Then the login view is visible
