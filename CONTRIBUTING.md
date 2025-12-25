# Contributing to BUSSter

Thank you for your interest in contributing to BUSSter! This is an open source hardware project, and we welcome contributions from the community.

---

## How to Contribute

### 1. Documentation
- Improve existing documentation
- Add build guides and tutorials
- Create diagrams and illustrations
- Write troubleshooting guides
- Translate documentation

### 2. Hardware Design
- Circuit improvements
- PCB layout optimization
- Component selection and testing
- Audio quality measurements
- Cost reduction ideas
- Alternative designs (budget vs. boutique)

### 3. Firmware Development
- Microcontroller code
- Scene management features
- Display interface improvements
- MIDI integration
- Testing and debugging

### 4. Testing
- Audio quality measurements (THD, noise, frequency response)
- Real-world guitarist testing
- Edge case discovery
- Long-term reliability testing
- Report bugs and issues

### 5. Tools and Utilities
- Simulation tools
- Configuration software
- Scene management apps
- Testing utilities

---

## Getting Started

1. **Read the docs**: Familiarize yourself with [VISION.md](VISION.md) and the README
2. **Check existing issues**: Look for issues labeled "good first issue" or "help wanted"
3. **Ask questions**: Open a discussion if you're unsure about something
4. **Start small**: Begin with documentation or small improvements

---

## Contribution Guidelines

### General Principles
- **Start simple**: Follow the project philosophy of iterative improvement
- **Document everything**: Code, circuits, and decisions should be well-documented
- **Test thoroughly**: Audio quality is critical - test before submitting
- **Communicate**: Discuss major changes before implementing

### Code Style
- Use clear, descriptive names for variables and functions
- Comment complex logic
- Follow existing code style in the project
- Include unit tests where applicable

### Hardware Contributions
- Provide schematics in KiCad format (preferred) with PDF exports
- Include detailed component specifications
- Document any design decisions and trade-offs
- Provide testing results and measurements

### Documentation
- Use clear, concise language
- Include diagrams and examples where helpful
- Follow Markdown formatting standards
- Update table of contents if adding new sections

---

## Submitting Changes

### Pull Request Process

1. **Fork the repository**
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**: Follow the guidelines above
4. **Test thoroughly**: Ensure your changes work as expected
5. **Commit with clear messages**: Describe what and why
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Open a pull request**: Provide a clear description of changes

### Pull Request Template

```
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Hardware design
- [ ] Firmware
- [ ] Other (please describe)

## Testing
How has this been tested?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation has been updated
- [ ] Changes have been tested
- [ ] All tests pass
- [ ] Commit messages are clear
```

---

## Reporting Issues

### Bug Reports
When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Hardware/software versions
- Photos or screenshots if relevant
- Measurements or test data if applicable

### Feature Requests
When suggesting features:
- Describe the use case
- Explain why it's valuable
- Consider the project philosophy (start simple)
- Acknowledge trade-offs or complexity

---

## Code of Conduct

### Be Respectful
- Be kind and respectful to all contributors
- Welcome newcomers and help them get started
- Provide constructive feedback
- Focus on the technical merits

### Be Professional
- Keep discussions on-topic
- Avoid personal attacks or inflammatory language
- Respect different opinions and approaches
- Give credit where credit is due

### Be Collaborative
- Share knowledge and expertise
- Help others learn and improve
- Celebrate community achievements
- Support the project's long-term success

---

## Project Structure

Understanding the repository structure will help you contribute effectively:

```
busster/
├── README.md              - Project overview
├── VISION.md              - Project vision and goals
├── LICENSE                - Dual license (CERN-OHL-P + MIT)
├── CONTRIBUTING.md        - This file
├── docs/                  - Technical documentation
├── hardware/              - Circuit designs, PCBs, BOMs
├── firmware/              - Microcontroller code
├── tools/simulators/      - Python simulation tools
└── archive/research/      - Historical research files
```

---

## License Agreement

By contributing to BUSSter, you agree that your contributions will be licensed under:
- **CERN-OHL-P v2** for hardware contributions
- **MIT License** for software contributions

See [LICENSE](LICENSE) for full details.

---

## Questions?

- **General questions**: Open a discussion on GitHub
- **Bug reports**: Open an issue
- **Major changes**: Discuss in an issue before implementing
- **Private inquiries**: Contact the maintainer (see README)

---

## Recognition

Contributors will be recognized in:
- Project documentation
- Release notes
- Credits section (coming soon)

We appreciate all contributions, whether big or small!

---

*Thank you for helping make professional-grade pedal routing accessible to everyone!*
