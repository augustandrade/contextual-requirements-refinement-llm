In this chapter, we elaborate on the use of natural language for documenting requirements, and: 

❑ Define the term “textual requirement”. 
❑ Sketch the key advantages and disadvantages of textual requirements. 
❑ Outline some key problems caused by non-atomic textual requirements. 
❑ Describe five kinds of ambiguity inherent in textual requirements. 
❑ Introduce techniques to mitigate the ambiguity of textual requirements.

In practice, requirements are commonly documented textually using natural language. We use the term “textual requirement” to refer to requirements which are documented or specified using natural language such as English, French, German, etc. We define the term “textual requirements”[31] as follows.

Definition 25-1: Textual Requirement (Natural Language Requirement) A textual requirement (artefact) is a requirement which is documented using a natural language.

25.1 Advantages and Disadvantages of Textual Requirements

Natural language allows the stakeholders to communicate and document nearly any kind of information and knowledge concerning the requirements for the system. The use of natural language in requirements engineering is essential to facilitate, for instance, the elicitation of requirements, the exchange of background information, or the development of new and innovative requirements. In general, the use of textual requirements has some key advantages (Kamsties, 2001): 

❑ Universal: The documentation of requirements in natural language is universal, since natural language can be used in any problem area or domain.

❑ Flexible: Natural language is flexible, since natural language allows arbitrary abstractions and refinements during requirements documentation. 

❑ Comprehensible: Requirements documented in natural language are comprehensible to many stakeholders, since (assuming the stakeholders know the language) no training or special tools are required. 

However, the use of textual requirements also has some key disadvantages: 

❑ Non-atomic requirements artefacts: Textual requirements quite often intermingle data, behavioural, functional, and quality aspects of requirements. In other words, different kinds of requirements are defined in a single, non-atomic requirements artefact. Due to the non-atomic definition, requirements can easily be overlooked, redundancy is typically introduced, and consistent change integration is significantly more difficult (see Section 25.2). 

❑ Ambiguity: Natural language is inherently ambiguous. Ambiguously documented requirements have more than one valid interpretation and therefore suffer from the risk that different stakeholders interpret a textual requirement differently. Even if specified carefully, the inherent ambiguity of natural language often leads to different interpretations of textual requirements and is thus a significant problem in practice (see Section 25.3). 

Besides ambiguity, gaps in requirements artefacts (i.e., underspecified requirements) are another common source of different interpretations. Stakeholders can make different assumptions about the not specified (missing) parts of a requirement and thus interpret the requirement artefact differently. This holds for textual requirements, but also in general for requirements artefacts documented using any kind of representation format. Among other things, a template-based specification can help to mitigate this problem. 

25.2 Non-Atomic, Intermingled Requirements Artefacts 

If requirements are documented using natural language, the three traditional perspectives (data, function, and behaviour) are often intermingled within a single requirements artefact. For example, the requirement described in Example 25-1 contains behavioural, data, and functional aspects which are not clearly identifiable in the textual requirement. In general, natural language (in contrast to conceptual models) does not support focusing on only one perspective (behaviour, data, or function) at a time and thereby, among other things, does not facilitate the handling of complexity. 

Example 25-1: Functional Requirements in Natural Language

R2: If the glass break detector of a window detects the pane has been damaged, the system shall inform the security service. 
Data/Structure: glass break detector, window, pane, system, security service 
Function: detects, inform the security service Behaviour: if […] damaged, then inform […]

Moreover, in textual requirements, also quality requirements can be intermingled with any (or all) of the three traditional perspectives (behaviour, data, and function). Thus, certain aspects of the requirements can easily be overlooked. Example 25-2 illustrates this by extending the requirement “R2” of Example 25-1 with a quality property.

Example 25-2: Intermingling of Function and Quality R2: If the glass break detector of a window detects the pane has been damaged, the system shall inform the security service within 2 seconds at the latest.

The quality defined in requirement R2 in Example 25-2 could easily be overlooked during testing and thus not be considered. Even if quality aspects are logically related to a functional, behavioural, or data aspect, those aspects should be defined in dedicated quality requirements, as illustrated in Example 25-3.

Example 25-3: Separation of Requirements Artefacts

Functional requirements: 
R-F-17: The glass break detector of the window shall detect if the glass pane is damaged. 
R-F-18: If the detector detects damage to the pane (see R-F-17), the system shall inform the security service. 
Quality requirement: 
R-Q-2: The system shall inform the security service (see R-F-18) within 2 s after detecting damage.

In general, the separate textual documentation of quality and functional requirements avoids the risk of overlooking and thus neglecting a requirements artefact. The same applies to constraints. Moreover, the separate definition of those artefacts avoids redundancies, compared to intermingling different aspects in the definition of the artefacts.

25.3 Ambiguity of Textual Requirements

Definition 25-2: Ambiguity Ambiguity of a word or expression occurs when the word or expression can be understood in more than one way.

In the following sections, we elaborate on four kinds of ambiguity (i.e., lexical, syntactic, semantic , and referential ambiguity) and ambiguity caused by the use of vague terms in the documentation — another source of ambiguity (based on Berry et al. (2003)). These kinds of ambiguity are not mutually exclusive; they may also occur in combination in a single textual requirements artefact.

25.3.1 Lexical Ambiguity

Lexical ambiguity is caused by words with more than one meaning and has the following three major causes:

❑ Synonyms: A synonym is a word (letter sequence), which has the same meaning as at least one other word. Examples of synonyms are “car/automobile”, “small/little”, and “sick/ill”. However, for one stakeholder two words might have the same meaning, whereas for another stakeholder the same words might have different meanings – which leads to ambiguity. 

❑ Homonyms: A homonym is a word that sounds or spells the same as another word, but has a different meaning. An example of a homonym is the word “trunk”. In botany, this word typically refers to the stem of a tree, while in zoology the same word “trunk” refers to the nasal extension emerging from an elephant’s face. Also, “trunk” is a typical description of a large, wooden chest, or luggage case, or, in American English, it can even refer to the rear cargo compartment of a motor vehicle. The term “homonym” merely refers to words with identical spelling and pronunciation. Words which merely sound identical but are spelled differently are called homophones. Examples of homophones are “right/rite” or “there/their/they’re”.

❑ Polysemy: Polysemy occurs when a word has several related but different meanings with the same etymology and is thus a special case of a homonym (Berry et al., 2003). For example, the word “wood” can mean a material made out of trees, a small forest, or a kind of golf club. All these meanings are in some way related to trees. A further special case of polysemy is systematic polysemy. Systematic polysemy is due to the lack of distinction which is commonly made between classes like type and unit, product and process, count and mass, etc. An example of the lack of distinction between process and product would be “Her writing was flawless.” Writing can here refer to the act of writing (process) or to what she has written (product). 

Synonyms, homonyms, and polysemy are thus a frequent source of ambiguity in requirements engineering and are caused, for example, by different stakeholder backgrounds or different vocabulary used for technical terms in different companies, different countries, or different departments within large organisations.

25.3.2 Syntactic Ambiguity

Syntactic ambiguity occurs if there are at least two valid syntax trees which can be assigned to the same sentence, and for each assignable syntax tree the sentence has a different meaning (see, for example, Hirst (1987)). Syntactic ambiguity is also referred to as structural ambiguity since a syntax tree denotes the grammatical structure of a sentence. Example 25-4 shows a textual requirement with syntactical ambiguity. 

Example 25-4: Syntactic Ambiguity of Textual Requirements 
R2: The user enters the access card with the access code 

Two different syntax trees can be associated with the requirement R2 shown in Example 25-4. Fig. 25-1 depicts these two syntax trees. The textual requirement R2 can thus be interpreted in two ways: 
❑ Interpretation 1: The user enters the access code by making use of the access card, i.e., the access card contains the access code. 
❑ Interpretation 2: The user enters the access card and, in addition, the access code into the system.

Example 25-5 shows another example of a syntactically ambiguous textual requirement. 

Example 25-5: Syntactic Ambiguity of Textual Requirements 

R21: The navigation system shall display the last five destinations and starting points. The syntactic ambiguity of requirement R21 in Example 25-5 is about which information the system shall display. One possible interpretation of requirement R21 is that the system shall display for each of the last five items entered the destinations or starting points. Another possible interpretation is that the system shall display the last five destinations and a set of starting points. A more detailed description of syntactic ambiguity of textual requirements can is provided by Berry et al. (2003).

25.3.3 Semantic Ambiguity

Semantic ambiguity occurs if a sentence has more than one interpretation even if it contains no lexical, syntactic, or referential ambiguity. Example 25-6 shows a semantically ambiguous textual requirement.

Example 25-6: Semantic Ambiguity of Textual Requirements R24: If a window of the car is damaged and the interior surveillance of the car detects an intruder or a door of the car is opened without a car key, the safety system shall raise an alarm.

Due to the missing information regarding whether “and” binds stronger than “or”, the requirement R24 of Example 25-6 can be interpreted differently. Example 25-7 depicts two possible interpretations of the requirement R24 of Example 25-6. The interpretations differ in the condition which leads to raising the alarm.

Example 25-7: Semantic Ambiguity of Textual Requirements

Possible interpretation 1: “and” stronger than “or”: [➊ and ➋] or ➌ If [➊ a window of the car is damaged and ➋ the interior surveillance of the car detects an intruder] or ➌ a door of the car is opened without a car key, the safety system raises an alarm. Possible interpretation 2: “or” stronger than “and”: ➊ and [➋ or ➌] If ➊ a window of the car is damaged and [➋ the interior surveillance of the car detects an intruder or ➌ a door of the car is opened without a car key], the safety system raises an alarm.

According to interpretation 1 (“and” binds stronger than “or”) shown in Example 25-7, opening a door of the car without a car key is sufficient to raise the alarm. In contrast, according to interpretation 2 (“or” binds stronger than “and”), a window of the car must have been damaged and, additionally, the interior surveillance system must detect an intruder or (alternatively) a door of the car must be opened without a car key to raise the alarm.

25.3.4 Referential Ambiguity

Referential ambiguity occurs if a word or phrase in a sentence refers to an object and there are different interpretations regarding what this object is. The term “refer” can have two different meanings: 

❑ The term “refer” can denote the relation between a symbol (or a word) and an object of the “real” world that is denominated by the symbol (see Section 26.3). With this interpretation of “refers”, the referential ambiguity is caused by different “real”-world objects that are related to the same word or phrase. 
❑ In linguistics the term “refer” denotes the relation between a word or phrase in a sentence and an expression (possibly in a different sentence) before or after this word or phrase. 

We elaborated on the first meaning in Section 25.3.1, and will thus focus on the second meaning in the following. In linguistics, an anaphor is an expression in a sentence which refers back to a previous expression in the same sentence or in a previous sentence. The expression referred to by the anaphor is called the antecedent. Referential ambiguity is caused if an anaphor refers to several antecedents. 

Example 25-8 depicts a requirement with referential ambiguity where two antecedents (“access card” and “personal identification number”) of the anaphor “it” in the second sentence cannot be determined unambiguously. It is unclear whether the pronoun “it” refers to the access card or to the personal identification number. Thus, the person interpreting the requirement does not know under which condition the access is denied: If the access card is invalid or if the entered PIN is invalid?


Example 25-8: Referential Ambiguity of Requirements

R42: The customer inserts the access card into the card reader and enters a personal identification number (PIN) at the keypad. If it is invalid, the system shall deny the access.

25.3.5 Vagueness of Terms

The different types of ambiguity are interrelated with another issue which hampers the unambiguous interpretation of textual language requirements, namely vagueness of terms. The definition of the “vagueness” of a term is based on the concept of the “extension” of a term explained below. 

The extension of a term is the set of all objects or phenomena which are denoted by this term. A term is considered vague if there is at least one known object for which it is impossible to determine whether the object belongs to the extension of the term or not. In this case, it is impossible to determine the extension of the term.

Example 25-9: Vagueness due to a Blurry Definition of a Term 
All medium-sized vehicles shall be equipped with a navigation system.

The statement in Example 25-9 contains vagueness (also called fuzziness) due to the expression “medium-sized vehicles”. There are vehicles for which it is impossible to unambiguously determine whether the vehicle is a medium-sized vehicle or not. One person might allocate a vehicle to the category of medium-sized vehicles while another person does not allocate the same vehicle to this category. Thus, the term “medium-sized vehicles” is not clearly defined. Vagueness can especially cause ambiguity if requirements are interpreted by stakeholders with different backgrounds. For example, the term “medium-sized vehicle” might have different meanings (extensions) in different countries (e.g., America, Germany, or India).

25.4 Techniques for Avoiding Ambiguity

In the following, we describe three common techniques for mitigating ambiguity of textual requirements: Glossaries, syntactic sentence patterns, and controlled languages. By applying these techniques, the risks related to the ambiguity of natural language requirements can be mitigated.

25.4.1 Glossaries

Lexical ambiguity is caused by homonyms, synonyms, and polysemy (see Section 25.3.1). This kind of ambiguity can be reduced or even completely avoided by explicitly defining the meaning of the terms used in a glossary. We define the term glossary as follows.

Definition 25-3: 
Glossary A glossary defines the specific meaning of terms which are part of a language (terminology). A glossary can additionally contain references to related terms as well as examples which explain the terms and put the terms into a context.

The definitions of the terms in a glossary typically follow a predefined structure. Hint 25-1 suggests such a structure which consists of the parts “term”, “definition”, “synonyms”, “related terms” (generalisations, specialisations, etc.), “examples/counter-examples”, and “scenarios”. In requirements engineering, examples and counter-examples can be provided, for example, by referring to scenarios where the term is used. Scenarios describe concrete examples of system usage and provide important context information which supports determining the correct interpretation of the terms (see Weidenhaupt et al. (1998)).

Explicitly defining important terms in a glossary helps reduce or even avoids the following risks: ❑ Some stakeholders do not know the meaning of a term and thus interpret the term differently. ❑ Different stakeholders interpret a term they are familiar with differently based on their backgrounds and knowledge. ❑ Different interpretations of a term exist but are not known. Often different interpretations of a term surface during the definition of the term in the glossary. ❑ Different stakeholders use different terms for the same real-world object or phenomenon, i.e., synonyms. ❑ Different stakeholders use the same term for several different real-world objects or phenomena (possibly related to each other), i.e., homonyms.

Hint 25-2: Creating a Glossary 
❑ Define a structure for the glossary entries to be used by all authors editing glossary entries. 
❑ Check the structure of the glossary frequently. 
❑ Ask stakeholders with different backgrounds to provide their own definition of a term and align the definitions collected.
❑ If you are not sure whether a term should be defined in the glossary, rather define the term than not. 
❑ Involve stakeholders with different backgrounds (from different context perspectives) to review the term definitions in the glossary, comment on existing definitions, and identify missing ones. 
❑ Make the glossary available to all stakeholders. 
❑ If possible, provide support for managing the glossary in the intra- or internet, for example, by establishing a wiki where stakeholders can comment on definitions and suggest new glossary entries (see, for example, Stricker et al. (2009)).

25.4.2 Syntactic Sentence Patterns

Syntactic sentence patterns help avoid frequent mistakes made when defining textual requirements. An example of such a mistake is the use of the passive voice. Syntactic sentence patterns define concrete syntactic structures for textual requirements (see also Rolland and Proix (1992), Rupp and Goetz (2000), Schienmann (2002)). We define the term “syntactic sentence pattern” as follows.

Definition 25-4: Syntactic Sentence Pattern

A syntactic sentence pattern defines a syntactic structure for sentences used in textual requirements. It also defines the meaning of each element of the syntactic sentence pattern.

The syntactic sentence pattern depicted in Fig. 25-2 consists of the following structural elements:

❑ <When?>/<Under what conditions?>: This element is used to define one or more logical or temporal conditions under which the function documented in the requirement shall be performed or provided. The use of this element is optional. 
❑ <System name>: This element defines the name of the system which shall provide the function. The phrase “the system” plus its concrete name constitutes the grammatical subject of the sentence. 
❑ ”Shall/Might/Should”: This element defines the importance of the requirement. The modal verb “shall” indicates a requirement that has to be implemented, while “should” indicates a requirement that is highly recommended but would not make the system unacceptable if it is not implemented. Using “might” indicates that implementation of the requirement is optional. One of these three modal verbs must be chosen. 
❑ <Process>: This element indicates the required functionality (called the “process” in Rupp (2021)). This functionality is documented by a full verb such as “print” or “transfer”. The syntactic sentence pattern depicted in Fig. 25-2 distinguishes three types of functionality and suggests a different pattern for each type: 
– The first pattern (<process>) applies to functionality the system shall offer independently of any interactions with users. 
– The second pattern (PROVIDE <whom?> WITH THE ABILITY TO <process>) applies to functionality the system shall provide to specific users. 
– The third pattern (BE ABLE TO <process>) is suggested for documenting functionality the system shall perform as a reaction to trigger events from other systems. 
❑ <Object>: This element describes the object for which the functionality is required, e.g., a type of document (order confirmation) to be printed. The object as well as additional, optional details about the object are the last elements of the syntactic sentence pattern (the end of the sentence).

Example 25-11 shows a textual requirement defined using the syntactic sentence pattern depicted in Fig. 25-2.

Example 25-11: Documentation of a Textual Requirement Based on a Syntactic Sentence Pattern 
R114: If the glass break detector detects the damaging of a window, the system “Intruder Alarm” shall inform the head office of the security service. 
[<When>: If the glass break detector detects the damaging of a window] THE SYSTEM [<system name>: “Intruder Alarm”] SHALL [<Process>: inform] [<Object>: the head office of the security service].

25.4.3 Controlled Languages

A controlled language is a technical language which imposes precisely defined constraints on natural language. It is used to document facts about a specific domain (such as finance or medical). The basic idea of defining and using a controlled language stems from Kamlah and Lorenzen (see Kamlah and Lorenzen (1996), Lorenzen (1973)). In computer science, Wedekind (1979) took up the idea of controlled languages in the domain of conceptual database design.

In contrast to traditional formal languages, a controlled language defines not only a formal grammar but also a vocabulary. The vocabulary takes the domain the language is designed for into account and defines a set of permissible terms to be used in the expressions documented using the language. The meaning of each term is defined a priori and therefore does not need to be determined from the context of the phrase or sentence in which it is used (in contrast to natural languages).

Compared to syntactic sentence patterns, a controlled language defines, in addition to the syntactic structures (syntax), also the semantics of the statements. Controlled languages can thus be regarded as an extension of syntactic sentence patterns.

We define the term controlled language as follows.

Definition 25-5: Controlled Language A controlled language defines, for a specific domain, a restricted natural language grammar (syntax) and a set of terms (including the semantics of the terms) to be used with the restricted grammar in order to document statements about the domain.

Using a controlled language in requirements engineering has the following advantages (see Ortner (1997), Schienmann (2002)):

❑ Expressions documented in a controlled language are easy to understand, since they are similar to expressions in natural language.
❑ Expressions documented in a controlled language are less ambiguous than expressions in natural language, since they have a simplified underlying grammar and a predefined vocabulary with precise semantics. 
❑ Expressions documented in a controlled language are semantically verifiable due to the formal grammar and the predefined terms.

The use of a controlled language thus improves the communication between stakeholders, since ambiguities and misunderstandings about aspects of the underlying domain are avoided. Although a controlled language restricts the grammar and vocabulary of the natural language, the controlled language still seems familiar, since it merely regularises the use of habitual language constructs (see Wedekind (1979)). 

Due to the imposed restrictions, a controlled language is less expressive than natural language. In addition, stakeholders require extensive training to enable them to apply the controlled language. However, a controlled language is well suited for specifying requirements (e.g., in system requirements specifications), especially when precisely delimited and well-understood domains are considered. 
Schienmann (2002) suggests a four-step approach for developing a controlled language: 
1. Elicitation of statements: During requirements elicitation, technical experts elicit a list of fact-related, colloquial statements, for example, by using interviews. 
2. Clarification and definition of technical terms: The requirements engineer learns the correct use of the technical terms from the technical experts, and defines formal rules for the technical terms. Example 25-12 depicts three typical rules for technical terms. The subordination rule stated in Example 25-12 expresses “employee” is a specialisation of “person”. The equivalence rule defines that “library card” and “user card” are synonyms, and the contrariness rule states that a real-world object cannot be a “software unit” and a “hardware unit” at the same time. In addition to the rules, the meaning of each technical term is defined in a glossary.

Example 25-12: Rules in Controlled Language Development Subordination: x ∈ employee ⇒ x ∈ person Equivalence: x ∈ library card ⇔ x ∈ user card Contrariness: x ∈ software unit ⇒ x ∉ hardware unit

3. Standardisation of statements:

Pattern types and syntactic sentence patterns for each pattern type are defined. The defined syntactic sentence patterns are used to document the requirements and statements about the domain. Tab. 25-1 depicts different pattern types, sentence patterns for each pattern type, and examples of standardised requirements statements created using the syntactic sentence patterns.

Tab. 25-1 Pattern types and corresponding syntactic sentence patterns

Type of pattern | Pattern | example
Participation | [Object] HAS AN [object] | User HAS A status
Inclusion | [Object] IS AN [object] | Periodical IS A collected edition
Partition | [Object] CONSISTS OF [object] | Collected edition CONSISTS OF single editions
Ability | [Person] CAN [action] | User CAN borrow book
Process | [Action] RESULTS FROM [action] | Indexing book RESULTS FROM inventorying book
Rule | IF [event] AND [condition] THEN [action] | IF book returned AND lending period exceed THEN reminder charges 

4. Classification of statements: The first three steps define the meanings of statements and terms. To facilitate the specification of requirements in a model-based format, the standardised statements are classified according to their type (e.g., modelling construct). Example 25-13 illustrates the classification of standardised statements using the patterns of the controlled language depicted in Tab. 25-1. The standardised expressions are “mapped” in Example 25-13 to static aspects of an object diagram (see Schienmann (2002) for details).

Example 25-13: Classification of Statements 
User HAS A user status ⇒ attribute Periodical IS A collected edition ⇒ inheritance relationship Collected edition CONSISTS OF single editions ⇒ aggregation User CAN borrow books ⇒ method

Pohl, Klaus. Requirements Engineering - Fundamentals, Principles and Techniques: Second Edition (p. 605). (Function). Kindle Edition. 