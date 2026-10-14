@customer-portal
Feature: Customer portal navigation

  @HU-103 @SOLV-227
  Scenario: A visitor without session lands on login
    Given the portal is open
    Then the customer login view is visible

  @HU-103 @SOLV-227
  Scenario: A signed-in customer who reopens login stays in the portal
    Given the customer is signed in
    When the customer opens the login page
    Then the user shell is visible

  @pendiente @HU-107 @SOLV-231
  Scenario: Destinations on desktop
    Given the customer is signed in on a 1440 canvas
    Then the top navigation shows Inicio, Pólizas, Siniestros and Perfil as text
    And "Nueva cotización" is a filled button, not an underlined destination

  @pendiente @HU-107 @SOLV-231
  Scenario: Hamburger menu on 390
    Given the customer is on a 390 canvas
    When the customer opens the menu
    Then the navigation menu shows the same four destinations
    And closing the overlay does not change the page

  @pendiente @HU-107 @SOLV-231
  Scenario: A nested page keeps its parent destination
    Given the customer is on the policy detail
    Then the Pólizas destination stays underlined
    And "Volver" returns to the policy list, not to Inicio

  @pendiente @HU-107 @SOLV-231
  Scenario: Issuance hides the navigation
    Given the customer accepted a valid offer
    When the customer is on Emitiendo or Póliza emitida
    Then the customer cannot change destination
