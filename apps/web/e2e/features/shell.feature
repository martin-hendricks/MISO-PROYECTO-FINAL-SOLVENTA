Feature: Portal shells
  Scenario: User and CMS shells share one site
    Given the portal is open
    Then the user shell is visible
    When the visitor opens the CMS shell
    Then the CMS shell is visible
