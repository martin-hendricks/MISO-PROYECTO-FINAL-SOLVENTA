@backoffice
Feature: Operator broadcasts a message

  Scenario: The operator previews and sends a message to everyone
    Given the broadcast audience includes Ana
    And an operador signed in to the back-office
    When the user opens the notificaciones destination
    Then the broadcast form shows the title limit
    When the operator writes "Mantenimiento" and "El domingo no habrá app"
    Then the broadcast preview mirrors that message
    When the operator sends the broadcast
    Then the broadcast result shows 2 sent
    And the broadcast history includes "Mantenimiento"
