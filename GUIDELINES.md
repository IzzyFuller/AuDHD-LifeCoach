# AuDHD LifeCoach Project Guidelines

## Language Guidelines

### Neurodiversity-Supportive Language
- **Use identity-first language**: Refer to "Autistic person," "ADHD person," or "AuDHD person" rather than "person with autism/ADHD/AuDHD"
- This reflects the understanding that neurodivergence is an integral part of identity, not a disease or condition that someone "has"
- Examples:
  - ✅ "AuDHD individuals benefit from..."
  - ❌ "People with AuDHD benefit from..."
  - ✅ "Autistic perspectives are valued in design"
  - ❌ "Perspectives of people with autism are valued in design"

## Development Standards

### Test-Driven Development (TDD)
1. **Write a failing test first** that describes the desired behavior
2. **Write minimal implementation code** to make the test pass
3. **Refactor** code while maintaining test coverage
4. Always run the tests before committing code changes to ensure everything still passes

### Clean Architecture Principles
- Maintain strict separation between layers:
  - **Core Domain**: Contains business entities and rules, completely framework-independent
  - **Use Cases**: Application-specific business rules
  - **Adapters**: Convert data between external systems and the application
  - **Frameworks/Drivers**: Connect to external systems

### Code Organization
- Domain entities should not depend on any external libraries or frameworks
- Flow of dependencies should point inward (toward domain core)
- No circular dependencies between layers

### Python Practices
- Follow PEP 8 style guidelines
- Use type annotations
- Include docstrings for all public methods and classes
- Keep functions small and focused on a single responsibility

## Contribution Process
- Create a feature branch for each new feature
- Always start with a failing test
- Request peer reviews before merging to main
- Keep PRs focused on single concerns