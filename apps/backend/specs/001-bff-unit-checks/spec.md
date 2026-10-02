# Feature Specification: Channel Gateways and Merge Checks

**Feature Branch**: `001-bff-unit-checks`

**Created**: 2026-10-01

**Status**: Draft

**Input**: User description: "Add the web and mobile channel gateways, and add an automated check that always exercises those two gateways when they change. Exercise any other existing backend domain only when that domain already has behavior checks. Do not build the partner channel or any domain service, and do not add new domain folders. Add the Contratos BFF payloads with mocked answers for now."

## Clarifications

### Session 2026-10-01

- Q: Which gateway should answer automatic payment, renew/modify/cancel, and providers with assistance? → A: Both gateways return the automatic-payment body. Only the web gateway accepts renew, modify, and cancel. The mobile gateway accepts the assistance request, and the web gateway returns the operations status.
- Q: Which mocked answers must each contract return in this feature? → A: The success example plus every alternate body already written on the Contratos BFF page. Slow is the degraded premium, not a pause.
- Q: Must the web gateway refuse a customer token on advisor and operator screens? → A: A customer token opens only customer screens. An advisor token opens the advisor portfolio, the client file, and assisted sale. An operator token opens the operator queue, renew/modify/cancel, and the assistance status. Any other mix is refused. The mobile gateway stays a customer channel.
- Q: Which branches must the automated check validate? → A: Gitflow. `develop` integrates features. `main` records production releases. A `feature/*` push, and a proposal into `develop`, `main`, `release/*`, or `hotfix/*`, runs a gateway only when that directory changed. A push to `develop`, `main`, `release/*`, or `hotfix/*` runs both gateways even when neither changed. Any other branch selects nothing. `support/` is not used.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Server decides access for web and mobile (Priority: P1)

A caller using the web channel, and a caller using the mobile channel, each reach Solventa through their own gateway. Each gateway answers the screen payloads in Contratos BFF with the success example and every alternate body that page already writes. It does not call a domain service, and it does not pause to imitate a slow dependency. Sign-in returns a mocked access token, refresh token, and expiry. Later calls confirm that token and the role the server granted. The mobile caller cannot widen that role by claiming a different one. When the answer includes money, the caller receives a numeric amount and a currency code, and formats them on the device.

**Why this priority**: Without these two gateways and their mocked screen payloads, neither channel can exercise its contract under a server-enforced role.

**Independent Test**: For each contract, submit the success example and each alternate body written on Contratos BFF, and compare the mock answer with that page.

**Acceptance Scenarios**:

1. **Given** a web caller who signs in with email, password, and a desk role of cliente, asesor, or operador, **When** the web gateway accepts the sign-in, **Then** it returns a mocked access token, refresh token, and expiry carrying that role.
2. **Given** a mobile caller who signs in with email and password only, **When** the mobile gateway accepts the sign-in, **Then** it returns the same kind of mocked tokens and does not take a role from the caller.
3. **Given** a caller with no valid token, **When** the caller uses any contract other than sign-in, token refresh, or registration, **Then** the gateway refuses the call.
4. **Given** a mobile caller with a valid customer token who also sends a role the server did not grant, **When** the caller uses the mobile gateway, **Then** the gateway ignores the sent role and applies only the customer role.
5. **Given** a customer token, **When** the caller opens the advisor portfolio, the client file, assisted sale, the operator queue, renew/modify/cancel, or the assistance status, **Then** the web gateway refuses the call.
6. **Given** an advisor token, **When** the caller opens the advisor portfolio, the client file, or assisted sale, **Then** the web gateway accepts the call. **When** the caller opens any other protected web screen, **Then** the web gateway refuses the call.
7. **Given** an operator token, **When** the caller opens the operator queue, renew/modify/cancel, or the assistance status, **Then** the web gateway accepts the call. **When** the caller opens any other protected web screen, **Then** the web gateway refuses the call.
8. **Given** a successful quote or automatic-payment answer, **When** the gateway responds, **Then** the amount is numeric, the currency is a separate code, and the body contains no preformatted money string.
9. **Given** a contract that Contratos BFF assigns to one channel, **When** the other gateway is asked for it, **Then** that gateway does not serve it.
10. **Given** the automatic-payment contract, **When** either gateway is asked with a customer token, **Then** both return the same mock body.
11. **Given** a renew, modify, or cancel request from an operator token, **When** it is sent to the web gateway, **Then** the gateway returns the policy body with the new state. The mobile gateway does not accept that command.
12. **Given** an assistance request from a customer token, **When** the mobile gateway accepts it, **Then** it returns a mocked registered assistance. **When** an operator asks the web gateway, **Then** the web gateway returns the assistance status and that status does not enter the operator claim queue.
13. **Given** a contract whose page writes an alternate body, **When** the caller submits that case with a token allowed for that screen, **Then** the gateway returns that body. A slow dependency is represented only by a degraded premium, and the call is not paused.

---

### User Story 2 - A gateway change is checked before merge (Priority: P2)

A contributor proposes a change to a channel gateway. Before the change can join `develop` or `main`, an automated check runs that gateway's behavior checks in isolation. A failed check, an empty check set, a gateway that cannot be loaded, or a check that pauses for a fixed time blocks the change. A reviewer still has to approve the change; the automated result does not replace that approval.

**Why this priority**: The team treats a change as unfinished until its behavior checks pass. This story makes that rule visible on the proposal.

**Independent Test**: Open a change proposal that touches only the web gateway, one that touches only the mobile gateway, and one that breaks a selected check, and read the pass or fail result.

**Acceptance Scenarios**:

1. **Given** a proposal that changes only the web gateway, **When** the automated check runs, **Then** it runs the web gateway's behavior checks and does not fail because some other domain has no checks.
2. **Given** a proposal that changes only the mobile gateway, **When** the automated check runs, **Then** it runs the mobile gateway's behavior checks and does not require the web gateway to have changed.
3. **Given** a change published on `develop`, `main`, a `release/*` branch, or a `hotfix/*` branch that changes neither gateway, **When** the automated check runs, **Then** it still runs both gateways' behavior checks.
4. **Given** a gateway selected to run whose behavior checks fail, collect nothing, cannot load the gateway, or pause for a fixed time, **When** the check finishes, **Then** the proposal is marked failed.
5. **Given** a gateway behavior check, **When** it runs, **Then** it uses stand-ins for identity and for downstream collaborators and does not contact an outside system, a database, a cache, or a message bus.
6. **Given** a finished check, **When** a reviewer opens the proposal, **Then** a record lists which checks passed or failed. A coverage summary may be attached, and a coverage number by itself does not fail the proposal.

---

### User Story 3 - Other domains are checked only when they already have checks (Priority: P3)

Other backend domains already exist as named areas, but they are not built in this change. If a proposal touches one of those areas and that area already contains behavior checks, those checks run under the same rules as the gateways. If the area has no checks, or has checks but cannot be loaded, the check skips that area, states why, and stays green. The first time that area gains checks, a later failure blocks the proposal. A newly added domain that follows the same presence rules is included without rewriting the check definition.

**Why this priority**: The gateways are the work of this branch. Failing the proposal because an unfinished domain has no checks would block that work. Ignoring a domain after it gains checks would hide regressions.

**Independent Test**: Propose a change that touches a domain with no checks, and a change that touches a domain whose checks fail, and compare the two results.

**Acceptance Scenarios**:

1. **Given** a proposal that changes a domain whose check folder is missing or empty, **When** the automated check runs, **Then** that domain is skipped, the reason is visible, and the proposal is not failed for that reason.
2. **Given** a proposal that changes a domain that has behavior checks but no runnable application, **When** the automated check runs, **Then** that domain is skipped and the reason is visible.
3. **Given** a proposal that changes a domain that has behavior checks and a runnable application, **When** those checks fail, **Then** the proposal is marked failed.
4. **Given** a domain that was previously skipped and later receives behavior checks, **When** a proposal changes that domain and a check fails, **Then** the proposal is marked failed.
5. **Given** a new domain that appears later with the same kind of presence markers as the current domains, **When** a proposal changes it, **Then** the existing check definition includes it without being rewritten.

---

### Edge Cases

- A proposal changes both gateways: each gateway's behavior checks run.
- A proposal changes a gateway and an untested domain: the gateway is checked; the domain is skipped; a gateway failure still fails the proposal; the skip does not.
- A selected gateway's check set collects zero cases: the proposal fails.
- A skipped domain collects nothing: the proposal does not fail because of that domain.
- An optional domain has checks but no package definition: the domain is skipped, not failed.
- A check pauses for a fixed time: the proposal fails, including when the pause is inside an optional domain that was selected to run.
- The mobile caller sends a role and also lacks a valid token: the gateway refuses the call before considering the sent role.
- A web sign-in names a role other than cliente, asesor, or operador: the gateway refuses the sign-in.
- A customer token opens the web quote, web issue and query, web traceability of automatic payment, the web mortgage offer, and the web home. It does not open assisted sale.
- An advisor or operator token used on the mobile gateway is refused. The mobile gateway accepts a customer token only.
- A gateway response includes no money: the amount and currency rule does not apply to that response.
- Registration and token refresh do not require an existing access token. Refresh sends only the refresh token. Logout has an empty body and requires the current session.
- The selfie never arrives. Registration on mobile sends only a life-check result of ok or no.
- A claim notice with no location is still accepted.
- Cancel, and an operator rejection, without a reason are refused.
- When the mortgage profile is not ready, the mock premium is marked degraded and uses the fallback amount. That is the only slow outcome, and the gateway does not pause.
- A line of business mentioned without a written body is not invented. Re-reading a quote by its id returns the same offer body. The policy detail adds the claim-guidance text to the policy body. A client file can be created without an id and can be deactivated.
- The policy list is the same body after the phone was offline. The gateway does not store that offline copy.
- The required check result stays green when every selected gateway check passes and every untouched or untested domain is skipped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a web channel gateway that serves only the web contracts named in FR-019.
- **FR-002**: The system MUST provide a mobile channel gateway that serves only the mobile contracts named in FR-020, using the narrower bodies on the Contratos BFF page.
- **FR-003**: Each gateway MUST refuse a call that does not carry a valid access token, except sign-in, token refresh, and registration.
- **FR-004**: Each gateway MUST apply the role granted on the server. Web sign-in MUST accept only the desk role cliente, asesor, or operador and carry that role in the mocked token. The mobile gateway MUST ignore a role supplied by the client and MUST accept only a customer token.
- **FR-024**: On the web gateway, a customer token MUST be limited to the web quote without a client id, web issue and query, web traceability of automatic payment, the web mortgage offer, and the web home. An advisor token MUST be limited to the advisor portfolio, the client file, and assisted sale. An operator token MUST be limited to the operator queue, renew/modify/cancel, and the assistance status. Any other mix MUST be refused.
- **FR-005**: A gateway response that includes money MUST present a numeric amount and a separate currency code and MUST NOT present a preformatted money string or a locale field.
- **FR-006**: Downstream work invoked by a gateway MUST be replaceable by a stand-in during behavior checks, so a check can run without the real collaborator.
- **FR-007**: A change proposal that modifies the web gateway MUST run that gateway's behavior checks before the change is eligible to merge.
- **FR-008**: A change proposal that modifies the mobile gateway MUST run that gateway's behavior checks before the change is eligible to merge.
- **FR-009**: A change published on `develop`, `main`, a `release/*` branch, or a `hotfix/*` branch that modifies neither gateway MUST still run both gateways' behavior checks. A push to a `feature/*` branch MUST run a gateway only when that directory changed.
- **FR-010**: When a gateway is selected to run, the proposal MUST fail if any of its behavior checks fail, if no check is collected, if the gateway cannot be loaded, or if a selected check pauses for a fixed time.
- **FR-011**: Gateway behavior checks MUST run without contacting an outside system, a database, a cache, or a message bus. Identity and downstream collaborators MUST be stand-ins.
- **FR-012**: The system MUST keep a readable record of pass and fail for each check that ran. A coverage summary MAY be stored. A coverage percentage MUST NOT, by itself, fail the proposal.
- **FR-013**: A backend domain other than the two gateways MUST be selected only when the proposal changes that domain and the domain already contains at least one behavior check.
- **FR-014**: A domain with no behavior checks, with checks but no runnable application, or without a package definition MUST be skipped. The skip reason MUST be visible, and the skip MUST NOT fail the proposal.
- **FR-015**: After a domain gains behavior checks, a failing check on a later proposal that changes that domain MUST fail the proposal.
- **FR-016**: A domain added later that follows the same presence rules as today's domains MUST be discovered by the existing check definition. The definition MUST NOT need to be edited to name that domain.
- **FR-017**: The team MUST record, for people to apply, that `develop` and `main` accept a change only when this check has passed and at least one other teammate has approved it. Proposals into `develop`, `main`, `release/*`, or `hotfix/*`, and publishes to `develop`, `main`, `release/*`, `hotfix/*`, or `feature/*`, MUST run the check under the selection rules in FR-009. This feature MUST NOT install a bot that applies that rule.
- **FR-018**: This feature MUST NOT add behavior, folders, or checks implementation for the partner channel or for any domain service. It MUST NOT add a performance, security-scan, channel-screen, or deployment check. It MUST NOT add a style or type gate unless that domain already requires one.
- **FR-019**: The web gateway MUST answer, with mocked bodies from Contratos BFF, these contracts: web sign-in, web registration, web quote, web issue and query, operator claim queue, web traceability of automatic payment, web mortgage offer, web home, advisor portfolio, client file, renew/modify/cancel, and the operations status of assistance.
- **FR-020**: The mobile gateway MUST answer, with mocked bodies from Contratos BFF, these contracts: mobile sign-in, mobile registration with life-check, mobile quote, accept/issue/wallet, claim notice with evidence and status, mobile mortgage offer, in-app validity notices, mobile home, push-token registration, automatic payment, and the customer assistance request.
- **FR-021**: Both gateways MUST return the same automatic-payment mock body. Only the web gateway MUST accept renew, modify, and cancel. Only the mobile gateway MUST accept the assistance request. Only the web gateway MUST return the operations status of assistance, and that status MUST NOT enter the operator claim queue.
- **FR-022**: Mock answers MUST follow the fields and enumerated values published on the Contratos BFF page. The page does not fix the address or the action name of each contract; those choices MUST NOT change the published bodies.
- **FR-023**: For each contract, the gateway MUST return the success body and every alternate body already written on the Contratos BFF page. Those alternates include a failed life check, revoked consent, a refused policy, a claim notice with no location, an operator rejection that requires a reason, a cancel that requires a reason, a degraded mortgage premium, a policy detail with claim guidance, a client file created without an id, and a deactivated client. The gateway MUST NOT pause to simulate a slow dependency. It MUST NOT invent a body the page only names.

### Key Entities *(include if feature involves data)*

- **Channel gateway**: The server-side entry for one channel. This feature has two: web and mobile. Each answers its Contratos BFF payloads with mocks and applies identity and role before answering protected contracts.
- **Caller identity**: Email and password at sign-in, then a mocked access token, refresh token, and expiry. The web token carries a desk role of cliente, asesor, or operador, and that role limits which web screens accept the token. A mobile token is a customer token. A role named by the mobile client is not part of this identity.
- **Screen contract**: One payload pair from Contratos BFF, assigned to the web gateway, the mobile gateway, or both as in FR-021. The body fields and enumerated values are fixed by that page.
- **Money fact**: A numeric amount and a currency code returned together so the channel can format them. It is not a display string and it does not include a locale.
- **Backend domain**: An existing named area of the backend other than the two gateways. It may or may not already contain behavior checks.
- **Change proposal**: A proposed modification to a gateway or a domain, reviewed before it joins `develop` or `main`.
- **Check result**: Pass, fail, or skip-with-reason for one gateway or domain on a proposal. Skip-with-reason does not fail the proposal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a set of proposals that change only the web gateway, 100% run the web gateway checks and 0% fail because another domain has no checks.
- **SC-002**: 100% of proposals whose selected gateway checks fail, collect nothing, cannot load the gateway, or pause for a fixed time are blocked from merge.
- **SC-003**: 100% of proposals that change only a domain with no behavior checks remain unblocked by that domain, and the skip reason is visible on the proposal.
- **SC-004**: After a domain has behavior checks, 100% of later proposals that change it and fail those checks are blocked.
- **SC-005**: In a review of gateway answers that include a price or an automatic payment, 100% expose a numeric amount and a separate currency code, and 0% expose a preformatted money string or a locale field.
- **SC-007**: 100% of the contracts named in FR-019 and FR-020 return the success body and every alternate body written for that contract, 0% of those answers depend on a domain service, and 0% pause to simulate a slow dependency.
- **SC-006**: In trials where a mobile caller sends a role the server did not grant, 100% of accepted calls use only the customer role, and 100% of calls without a valid customer token are refused.
- **SC-008**: 100% of web calls that use a token outside the screens in FR-024 are refused, and 100% of calls inside those screens are accepted.

## Assumptions

- Integration follows Gitflow. `develop` integrates features. `main` records production releases. `feature/*` starts from `develop` and merges only into `develop`. `release/*` starts from `develop` and merges into `main` and back into `develop`. `hotfix/*` starts from `main` and merges into `main` and into `develop`, or into the open `release/*`. The automated check follows FR-009 and FR-017. `support/` is not used.
- Sign-in returns mocked tokens. This feature does not call an identity service. Mock sign-in accepts any email and password, grants the requested web role when that role is allowed, and grants a customer token on mobile. A token stays valid until its stated expiry. Protected contracts check that token and the role inside it.
- "Narrower" mobile responses means the mobile bodies published on Contratos BFF, which omit web-only back-office fields. The phone keeps its own offline copy of the policy list; the gateway has one body for that list.
- Contratos BFF is the field catalog at the Solventa wiki page of that name. This feature mocks every contract on that page. It does not add a contract the page does not list.
- Stand-ins are supplied by the behavior check. They are not extra products.
- "A check pauses for a fixed time" means the check sleeps instead of waiting for an actual outcome.
- Partner-channel work, domain-service work, load and failure-injection experiments, security scans, channel screen checks, and deployment are out of scope for this feature.
- Packaging of each gateway, and the rule that every new development includes behavior checks, already stand in the backend constitution. This specification states the outcomes; it does not restate the package layout.
- No automated agent will change repository settings. A short note for reviewers is enough to record the approval rule in FR-017.
- Discovery of a domain uses the markers already present for today's areas (a package definition or a short description). A later domain is included when it carries those same markers.
