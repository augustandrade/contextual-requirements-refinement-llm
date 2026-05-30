
In this chapter, we: 
❑ Define the terms “requirement” and “requirements artefact”. 
❑ Differentiate between three types of requirements: functional requirements, quality requirements, and constraints. 
❑ Introduce the ISO/IEC SQuaRE framework. ❑ Elaborate on the quality models and quality characteristics defined in the ISO/IEC SQuaRE framework. 
❑ Elaborate and illustrate the impact of constraints on the satisfiability of requirements. 
❑ Strongly recommend not to use “non-functional” requirements.

3.1 Definition

There are many different definitions of the term “requirement” which emphasise different aspects, but also partially overlap. For example, in the Glossary of IREB (International Requirements Engineering Board) (Glinz 2024, p. 21) a requirement is defined as

❑ “Need perceived by a stakeholder”. 
❑ “Capability or property that a system shall have”. 
❑ “Documented representation of a need, capability or property”.

The IREB definition is very similar to the definition of the IEEE 610.12-1990 standard[1] (IEEE Std 610.12, 1990, p. 62):

Pohl, Klaus. Requirements Engineering - Fundamentals, Principles and Techniques: Second Edition (p. 66). (Function). Kindle Edition. The IREB definition is very similar to the definition of the IEEE 610.12-1990 standard[1] (IEEE Std 610.12, 1990, p. 62):

1. “Condition or capability needed by a user to solve a problem or achieve an objective”. 
2. “Condition or capability that must be met or possessed by a system or system component to satisfy a contract, standard, specification, or other formally imposed documents”. 
3. “Documented representation of a condition or capability as in (1) or (2)”.

The current standard of the systems and software engineering vocabulary, ISO/IEC/IEEE 24765, defines requirements based on different standards as follows (ISO/IEC/IEEE 24765, 2017, p. 380):[2]

1. "Statement that translates or expresses a need and its associated constraints and conditions”. 
2. “Condition or capability that must be met or possessed by a system, system component, product, or service to satisfy an agreement, standard, specification, or other formally imposed documents”. 
3. “Provision that contains criteria to be fulfilled”. 
4. “Condition or capability that must be present in a product, service, or result to satisfy a contract or other formally imposed specification”.

Although the definitions use different wordings, those definitions share a lot of commonalities. In the definition of IREB – as well as in practical use – the term “requirement” is often used as a homonym to refer to both (1) the requirement itself (e.g., a condition or capability required by a stakeholder or other system), as well as (2) the documented requirement. Thus, when talking about a requirement, it is often unclear whether the documented requirement is meant, or whether the term requirement refers to the needs and desires of a stakeholder. To avoid different interpretations of the term “requirement” we differentiate between requirements and requirements artefacts (documented requirements) and define the two terms as follows.

Definition 3-1: Requirement

A requirement is either 
(1) a need or desire perceived by a stakeholder to solve a problem or to achieve an objective, 
(2) a capability or property that a system shall offer, or 
(3) a condition the system or its development shall satisfy.

Definition 3-2: Requirements Artefact

A requirements artefact is a documented requirement.

While the term “requirements artefact” always refers to a documented requirement, the term “requirement” refers to (1) needs and goals of stakeholders, (2) capabilities and properties the system shall offer which result, for example, from organisational needs, contracts, laws, or standards, and (3) conditions the system or its development shall satisfy, which are typically defined as constraints.

3.2 Three Types of Requirements We differentiate between three types of requirements:


3.2.1 Functional Requirements

Pohl, Klaus. Requirements Engineering - Fundamentals, Principles and Techniques: Second Edition (p. 68). (Function). Kindle Edition. 
Definition 3-3: Functional Requirement A functional requirement is a (1) “statement that identifies what results a product or process shall produce.” (2) “requirement that specifies a function that a system or system component shall perform.” (ISO/IEC/IEEE 24765, 2017, p. 195)

The standard nicely separates two distinct ways of defining functional requirements: by defining system inputs and outputs, or by explicitly describing a procedure to be realised by the system. Example 3-1 illustrates typical functional requirements for different systems.

Example 3-1: Functional Requirements FR-2 The electronic door locking system shall generate monthly reports containing all granted and denied admittances to the building. FR-3 If the user enters a correct PIN (personal identification number) at the keypad, the system shall open the door and record the granted access (record the date and time of the access, and the name of the PIN owner). FR-6 If a sensor detects a broken or damaged glass pane, the

Traditionally, functional requirements are documented using three complementary, partially overlapping perspectives: the data, the functional, and the behavioural perspectives. We elaborate on these three perspectives in Part IV.c.

3.2.2 Quality Requirements

Quality requirements define quality properties of the system to be developed such as the demanded level of system performance or the reliability expected from the system. Often, a quality requirement defines a quality property for the entire system. However, a quality requirement may also define quality properties for a particular service, functionality, or system component. 
If quality requirements are “not clearly defined, they can be viewed, interpreted, implemented and evaluated differently by the relevant stakeholders. This can result in systems that are inconsistent with user expectations and of poor quality; and time and cost overruns to rework the system. Therefore quality requirements for the system need to be specified clearly at the earliest stage of the development” (ISO/IEC 25030, 2019). 
Quality requirements are in many cases architectural drivers and thus have a significant influence on the system architecture (see, for example, Bass et al. (2013), Clements et al. (2002), Gorton (2006)). We define quality requirements as follows.

Definition 3-4: Quality Requirement A quality requirement defines a specific quality property of the entire system, a system component, a service, or a system function.

Example 3-2 illustrates typical quality requirements and indicates their type according to different quality properties.

Example 3-2: Different Kinds of Quality Requirements 
QR-12 The system shall reduce the average order processing time by 10 percent compared to the predecessor system. (type of quality property: efficiency) 
QR-15 The release of the locking mechanism shall take 0.8 seconds at most. (type of quality property: performance) 
QR-17 The user password stored in the system shall be protected against unauthorised access. (type of quality property: security)


Quite frequently, quality requirements defined for a software-intensive system influence each other. For example, efficiency requirements are typically in conflict with other quality requirements such as portability or maintainability. Thus, the relationships between quality requirements have to be considered, in order to support the handling of such conflicts.

very comprehensive introduction to software quality, quality properties, and the corresponding quality requirements is given by Wiegers and Beatty (2013), who distinguish between: 
❑ External quality properties, which can be observed and experienced by the end-user. They include: availability, installability, integrity, interoperability, performance, reliability, robustness, safety, security, usability. 
❑ Internal quality properties, which affect the quality of the system but are not directly observable by the end-user. They include: efficiency, modifiability, portability, reusability, scalability, verifiability.

ISO/IEC emphasises the importance of identifying and specifying quality requirements as part of the system and software development process. The comprehensive System and Software Quality Requirements and Evaluation (SQuaRE) framework is defined in the ISO/IEC 25030 (2019) standard. We briefly introduce the SQuaRE framework in Section 3.3 and elaborate on the quality model division of the SQuaRE framework in Section 3.4.

3.2.3 Constraints

Constraints restrict the development of the system, and often also restrict the properties a system can offer. Similarly to functional and quality requirements, constraints need to be elicited and documented during requirements engineering. 
Constraints are, among other things, imposed by organisational processes and guidelines (e.g., quality procedures to be followed), contracts (e.g., maximum resources to be spent), laws, and standards, or by the environment the system shall operate in (e.g., physical laws). Constraints can thus rarely be changed by the stakeholders during requirements engineering. We define the term “constraint” as follows.

Definition 3-5: Constraint A constraint is an organisational or technological requirement which restricts the way the system shall be developed, and/or the functions, qualities, and properties of the system itself. Based on Robertson and Robertson (2013)

Robertson and Robertson (2013) distinguish between solution constraints mandating technical design restrictions on the system itself (e.g., hardware platforms) and project constraints focusing merely on the development time and budget. Alternatively, constraints can be differentiated by their origin. For instance, one can distinguish the following types of constraints:

❑ Cultural constraints originate from the cultural background of the system users. An example of a cultural constraint is the constraint C-3 described in Example 3-3. 
❑ Legal constraints originate from laws and standards. An example of a legal constraint is the constraint C-4 described in Example 3-3. 
❑ Organisational constraints originate from organisational processes and guidelines. An example of an organisational constraint is the constraint C-1 described in Example 3-3. 
❑ Physical constraints originate from the environment the system shall operate in. An example of a physical constraint is the constraint C-2 described in Example 3-3. 
❑ Project constraints originate from the development contract and/or the project definition. Examples of project constraints are the constraints C-5 and C-6 described in Example 3-3.

Example 3-3: Different Types of Constraints 
C-1 Due to current conditions defined by the insurance company, only the security technician is allowed to deactivate the control function of the system. (organisational constraint) 
C-2 A fire protection requirement demands that the terminals in the sales rooms do not exceed the size 120 cm (height) × 90 cm (width) × 20 cm (depth). (physical constraint) 
C-3 The user interface shall not contain symbols or graphics abusive in any culture. (cultural constraint) 
C-4 The system shall process personal data in compliance with the EU’s Data Protection Directive 95/46/EC. (legal constraint) 
C-5 The effort for system development shall not exceed 480 person months. (project constraint) 
C-6 The system must be developed using the Rational Unified Process. (project constraint)

More details about different types of constraints can be found, for instance, in Schienmann (2002), and Kotonya and Sommerville (1997).

3.5 Impact of Constraints

Restrictions on Realisation Alternatives 

Each constraint defines a potential restriction on the realisation of functional and quality requirements of the system (see Gause (2005)). In other words, constraints restrict the number of valid (possible) alternatives for realising a (functional or quality) requirement and, consequently, the number of alternatives feasible for realising the entire system. Two extreme situations can occur with respect to the restricting effect of constraints. On one extreme, a constraint could prohibit a requirement or set of requirements from being realised, i.e., it can eliminate all possible realisation options. On the other extreme, a constraint might not restrict the realisation alternatives of any requirement at all.

3.6 So-Called Non-functional Requirements (NFRs)

In the 1990s it was quite common to differentiate between functional requirements and non-functional requirements (see, among others, Davis (1993), Chung et al. (2000), Kotonya and Sommerville (1997)). Even nowadays, differentiation between functional and non-functional requirements (NFRs) is, unfortunately, quite common – at least in industry. 
Examples
Typical examples of non-functional requirements defined in requirements specifications include: “the user interface should be user-friendly”, “the system should be easy to use”, or “the system shall be secure”. Such requirements are often explicitly categorised as non-functional requirements. Obviously, those non-functional requirements are only weakly specified – a possible indication that they are not sufficiently understood. For example, “the system shall be secure” allows many different interpretations and thus different answers to questions such as:

❑ What does the adjective “secure” mean? 
❑ Which properties shall the system provide in order to be “secure”? 
❑ Which functionality the system offers should be “secure”? 
❑ Which data the system deals with should be “secure”? 
❑ How to validate whether the realised system is “secure”?

Thus, expectations about functions and qualities the system should provide (to be secure) could differ widely. Thus, the likelihood that the realised system meets the expectations of the different stakeholders is low. Moreover, it is impossible to objectively prove or check whether the system fulfils this requirement.

Need to Refine Non-Functional Requirements

In general, a non-functional requirement (NFR) represents either: 
❑ Underspecified functional requirements. 
❑ Underspecified quality requirements. 
❑ Both underspecified functional and quality requirements. 

In all three cases, we strongly recommend refining the underspecified non-functional requirement into a (set of) fully specified functional requirement(s), and to explicitly specify the quality requirement(s) hidden behind the underspecified non-functional requirement. In many cases a documented non-functional requirement hides both functional and quality requirements. 
By refining a non-functional requirement into concrete functional and quality requirements, measurable system properties are defined unambiguously. For example, the underspecified non-functional requirement “the system shall be secure” could be refined into a set of refined functional and quality requirements (see Example 3-6). Depending on the system being developed and its context the refinement of the non-functional requirement could of course result in a very different set of functional and quality requirements.

Quite surprisingly, underspecified non-functional requirements are often not refined in practice. Requirements specifications often pass the quality gates, even if they contain underspecified non-functional requirements. It seems commonly accepted that non-functional requirements are not specified precisely and are vague. This leads to a tendency to accept underspecified non-functional requirements. As a consequence, a final requirements specification, which constitutes the basis for contracting the system development, contains underspecified and vague requirements. 

To conclude, we strongly recommend avoiding the category of “non-functional” requirements when writing requirements specifications. Instead, use the three types of requirements introduced in Section 3.2, namely functional requirements, quality requirements, and constraints 

Whenever a requirement is declared as “non-functional”, check carefully whether this requirement is underspecified. If so, you should refine it into a set of functional requirements, quality requirements or both (see also Hint 3-1).

Hint 3-1: How to Deal with “Non-Functional” Requirements 
❑ Avoid the category “non-functional” requirements in a requirements specification. Using the term “non-functional requirements” leads to a wrong classification of requirements. 
❑ Instead, differentiate between functional requirements and (specific types of) quality requirements (see Section 3.2). 
❑ For each “non-functional” requirement, check whether it is underspecified and conceals a set of functional and/or quality requirements. ❑ Refine each underspecified “non-functional” requirement into an adequate set of functional requirements, quality requirements, or both.

Pohl, Klaus. Requirements Engineering - Fundamentals, Principles and Techniques: Second Edition. (Function). Kindle Edition. 