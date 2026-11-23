@access @HU-103 @SOLV-227
Feature: Customer sign-in

  Scenario: Valid credentials open the customer home
    Given the customer login page is open
    When the customer signs in with valid credentials
    Then the customer lands on Inicio
    And the current page has no accessibility violations

  Scenario: Invalid credentials stay on the login view
    Given the customer login page is open
    When the customer signs in with invalid credentials
    Then the login view shows the credentials error without leaving
    And the current page has no accessibility violations

  Scenario: A network failure stays on the login view
    Given the customer login page is open
    When the customer signs in while the network is down
    Then the login view shows the network error without leaving
    And the current page has no accessibility violations
