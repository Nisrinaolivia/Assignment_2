"""Statutory text of the relevant provisions of the Privacy Act 1988 (Cth),
fed to the AI at each step of the assessment.

Source: Privacy Act 1988 (Cth), Federal Register of Legislation
(https://www.legislation.gov.au/C2004A03712/latest), Compilation No. 104 (4 June 2026).
Notes and the subsections of s 26WF that deal only with notifying particular
individuals have been omitted, as they are not relevant to whether an eligible
data breach exists.

This module can later be expanded into a small RAG database (as in Lab 2),
e.g. by adding extracts from the OAIC's Data Breach Preparation and Response guide.
"""

# ---------------------------------------------------------------------------
# Shared provisions
# ---------------------------------------------------------------------------

PERSONAL_INFORMATION = """Privacy Act 1988 (Cth) s 6(1) (definition):
personal information means information or an opinion about an identified individual,
or an individual who is reasonably identifiable:
(a) whether the information or opinion is true or not; and
(b) whether the information or opinion is recorded in a material form or not."""

S_26WE_2 = """Privacy Act 1988 (Cth) s 26WE Eligible data breach

(2) For the purposes of this Act, if:
    (a) both of the following conditions are satisfied:
        (i) there is unauthorised access to, or unauthorised disclosure of, the information;
        (ii) a reasonable person would conclude that the access or disclosure would be
             likely to result in serious harm to any of the individuals to whom the
             information relates; or
    (b) the information is lost in circumstances where:
        (i) unauthorised access to, or unauthorised disclosure of, the information is
            likely to occur; and
        (ii) assuming that unauthorised access to, or unauthorised disclosure of, the
             information were to occur, a reasonable person would conclude that the
             access or disclosure would be likely to result in serious harm to any of
             the individuals to whom the information relates;
then:
    (c) the access or disclosure covered by paragraph (a), or the loss covered by
        paragraph (b), is an eligible data breach of the entity; and
    (d) an individual mentioned in subparagraph (a)(ii) or (b)(ii) is at risk from
        the eligible data breach.

(3) Subsection (2) has effect subject to section 26WF."""

S_26WG = """Privacy Act 1988 (Cth) s 26WG Whether access or disclosure would be likely,
or would not be likely, to result in serious harm—relevant matters

For the purposes of this Part, in determining whether a reasonable person would
conclude that an access to, or a disclosure of, information:
    (a) would be likely; or
    (b) would not be likely;
to result in serious harm to any of the individuals to whom the information relates,
have regard to the following:
    (c) the kind or kinds of information;
    (d) the sensitivity of the information;
    (e) whether the information is protected by one or more security measures;
    (f) if the information is protected by one or more security measures—the
        likelihood that any of those security measures could be overcome;
    (g) the persons, or the kinds of persons, who have obtained, or who could
        obtain, the information;
    (h) if a security technology or methodology:
        (i) was used in relation to the information; and
        (ii) was designed to make the information unintelligible or meaningless to
             persons who are not authorised to obtain the information;
        the likelihood that the persons, or the kinds of persons, who:
        (iii) have obtained, or who could obtain, the information; and
        (iv) have, or are likely to have, the intention of causing harm to any of
             the individuals to whom the information relates;
        have obtained, or could obtain, information or knowledge required to
        circumvent the security technology or methodology;
    (i) the nature of the harm;
    (j) any other relevant matters."""

S_26WF = """Privacy Act 1988 (Cth) s 26WF Exception—remedial action

Access to, or disclosure of, information
If:
    (a) there is an access to, or a disclosure of, information held by an entity; and
    (b) the entity takes action in relation to the access or disclosure; and
    (c) the action is taken before the access or disclosure results in serious harm
        to any of the individuals to whom the information relates; and
    (d) as a result of the action, a reasonable person would conclude that the access
        or disclosure would not be likely to result in serious harm to any of those
        individuals;
then the access or disclosure is not, and is taken never to have been, an eligible
data breach of the entity or of any other entity.

Loss of information: action taken before any unauthorised access or disclosure
If:
    (a) information held by an entity is lost; and
    (b) the entity takes action in relation to the loss; and
    (c) the action is taken before there is unauthorised access to, or unauthorised
        disclosure of, the information; and
    (d) as a result of the action, there is no unauthorised access to, or
        unauthorised disclosure of, the information;
then the loss is not, and is taken never to have been, an eligible data breach of
the entity or of any other entity.

Loss of information: action taken after unauthorised access or disclosure
If:
    (a) information held by an entity is lost; and
    (b) there is unauthorised access to, or unauthorised disclosure of, the
        information; and
    (c) the entity takes action in relation to the access or disclosure; and
    (d) the action is taken before the access or disclosure results in serious harm
        to any of the individuals to whom the information relates; and
    (e) as a result of the action, a reasonable person would conclude that the access
        or disclosure would not be likely to result in serious harm to any of those
        individuals;
then the loss is not, and is taken never to have been, an eligible data breach of
the entity or of any other entity."""

# ---------------------------------------------------------------------------
# Law passed to the AI at each step
# ---------------------------------------------------------------------------

# Step 2: unauthorised access, disclosure or loss of personal information
ELEMENT_1_LAW = "\n\n".join([PERSONAL_INFORMATION, S_26WE_2])

# Step 3: likely serious harm (s 26WE(2)(a)(ii) / (b)(ii), applying the s 26WG factors)
ELEMENT_2_LAW = "\n\n".join([S_26WE_2, S_26WG])

# Step 4: remedial action exception
ELEMENT_3_LAW = "\n\n".join([S_26WE_2, S_26WF])