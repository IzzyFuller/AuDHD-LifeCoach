# AuDHD-LifeCoach
I was messaging with a friend the other day around 11:45 and I told them I would come over to their home at 15:30 and give them and their kid a ride to an event. They NEEDED to leave their house at between 15:30 and 16:00. My ADHD brain, however decided in that moment between sending that message and scheduleing my day from that point forward, to changed "arriving at their house at 15:30" to "leaving my house at 15:30" and thus I was very very late. I felt terrible, and while I strive to understand and accept my neurotype and how it is no worse or better than any other neurotype, this kind of Executive Function failure tweaks my internalized ableism badly. I wish I had supports to help with the social aspects of this social disability.

I wish an AI ADHD assistant had been monitoring my messages and had added a reminder to my calendar, or enabled an alarm to tell me to leave at the right time. So I am going to build one! My overall idea is that there would be a process running on my phone that would be listening to what I say all the time and monitoring messages I send to other people and could infer things from this data to automatically add reminders to my calendar, alarms to my clock, and tasks to a ToDo list or other work management tool (think as simple as Keep to as sophisticated as Jira, eventually). 

Eventually, I'd like it to be able to learn about me in particular and get better and better at understanding when I especially need help, nagging, and even some direct assistance ("would you like me to call the mechanic and schedule an oil change? your Mitsubishi is overdue!"). 

I would also like to include support for my various 'fun' autism tendencies such as monitoring the environment, and possibly my metabolic state and warning me if I might be experiencing too much sensory input and might be at risk of meltdown etc.

## Architecture

The AuDHD-LifeCoach application follows a clean architecture approach with clear separation of concerns. The diagram below illustrates the key components and how they interact with each other:

```mermaid
classDiagram
    %% Core Domain Entities
    namespace core.domain.entities {
        class Communication {
            +timestamp: datetime
            +content: string
            +sender: string
            +recipient: string
        }
        
        class Commitment {
            +when: datetime
            +who: string
            +what: string
            +where: string
            +calculate_departure_time()
        }
        
        class Reminder {
            +when: datetime
            +message: string
            +priority: string
            +acknowledged: bool
            +commitment: Commitment
            +from_commitment(commitment): Reminder
            +acknowledge()
            +snooze(duration)
            +is_due(): bool
        }
    }
    
    %% Core Interfaces
    namespace core.interfaces {
        class CommitmentIdentifiable {
            <<interface>>
            +identify_commitments(communication): List[Commitment]
        }
    }
    
    %% Adapters
    namespace adapters.ai {
        class HuggingFaceONYXTransformerCommitmentIdentifier {
            -model_name: string
            -_ner_pipeline
            +ner_pipeline
            +identify_commitments(communication): List[Commitment]
            -_extract_time_entities(text): List[Dict]
            -_has_commitment_intent(text): bool
        }
    }
    
    %% External Dependencies
    namespace external {
        class TransformersLibrary {
            <<external>>
            +pipeline()
        }

        class Dateparser {
            <<external>>
            +parse()
        }
    }
    
    %% Application Services
    namespace application.services {
        class CommunicationProcessor {
            -commitment_identifier: CommitmentIdentifiable
            +process_communication(communication): List[Reminder]
        }
    }
    
    %% Relationships - Core Dependencies
    core.interfaces.CommitmentIdentifiable <|.. adapters.ai.HuggingFaceONYXTransformerCommitmentIdentifier : implements
    
    %% Relationships - Source Code Dependencies
    adapters.ai.HuggingFaceONYXTransformerCommitmentIdentifier ..> core.interfaces.CommitmentIdentifiable : imports
    adapters.ai.HuggingFaceONYXTransformerCommitmentIdentifier ..> core.domain.entities.Communication : imports
    adapters.ai.HuggingFaceONYXTransformerCommitmentIdentifier ..> core.domain.entities.Commitment : imports
    application.services.CommunicationProcessor ..> core.interfaces.CommitmentIdentifiable : imports
    application.services.CommunicationProcessor ..> core.domain.entities.Communication : imports
    application.services.CommunicationProcessor ..> core.domain.entities.Reminder : imports
    core.domain.entities.Reminder ..> core.domain.entities.Commitment : imports
    
    %% Relationships - Runtime Dependencies
    core.domain.entities.Communication <-- adapters.ai.HuggingFaceONYXTransformerCommitmentIdentifier : analyzes
    adapters.ai.HuggingFaceONYXTransformerCommitmentIdentifier --> core.domain.entities.Commitment : produces
    core.domain.entities.Commitment <-- core.domain.entities.Reminder : references
    core.domain.entities.Commitment <.. core.domain.entities.Reminder : creates via from_commitment()
    
    application.services.CommunicationProcessor o-- core.interfaces.CommitmentIdentifiable : uses
    application.services.CommunicationProcessor --> core.domain.entities.Communication : processes
    application.services.CommunicationProcessor --> core.domain.entities.Reminder : produces
    
    %% External Library Dependencies
    adapters.ai.HuggingFaceONYXTransformerCommitmentIdentifier ..> external.TransformersLibrary : uses
    adapters.ai.HuggingFaceONYXTransformerCommitmentIdentifier ..> external.Dateparser : uses
```

### Key Components

- **Core Domain Entities**:
  - `Communication`: Represents messages sent/received that may contain commitments
  - `Commitment`: Represents obligations extracted from communications (meetings, appointments, etc.)
  - `Reminder`: Represents notifications created from commitments

- **Core Interfaces**:
  - `CommitmentIdentifiable`: Interface for components that can identify commitments in communications

- **Adapters**:
  - `HuggingFaceONYXTransformerCommitmentIdentifier`: Implementation that uses NLP (Natural Language Processing) to identify commitments in text

- **Application Services**:
  - `CommunicationProcessor`: Orchestrates the flow from Communications to Reminders

- **External Dependencies**:
  - `TransformersLibrary`: Hugging Face's transformers for NLP
  - `Dateparser`: Library for parsing date/time expressions in natural language

### Flow

1. A `Communication` (message) is received
2. The `CommunicationProcessor` passes it to a `CommitmentIdentifiable` implementation
3. The implementation (e.g., `HuggingFaceONYXTransformerCommitmentIdentifier`) extracts any `Commitment`s
4. The `CommunicationProcessor` creates `Reminder`s from these commitments
5. The system notifies the user about these reminders at appropriate times
