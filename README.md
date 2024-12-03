
# TradeStatEngine 📊
TradeStatEngine is a tool designed to import trading journal data and generate detailed statistics and visualizations to analyze your trading performance.

## Contribution 🙌
This project is actively maintained as per the developer's needs and availability. Contributions, suggestions, and feedback are highly encouraged to make this tool more accessible and user-friendly. Please feel free to submit pull requests or raise issues for improvements.

## Requirements
Install all dependencies using:
```bash
pip install -r requirements.txt
```

## How to Use 🚦

1. **Set up the Database**:
   - Run the `database_utils.py` script to initialize the database.
   - Create one or more accounts using the same utility.

2. **Prepare Your Journal Entries**:
   - Use the provided markdown template (`Template ✅⭕🟡⛔⬆️⬇️.md`) to format your trading journal entries.
   - Ensure all required fields match the template format.
   - **Note**: This tool is not inherently compatible with any specific app. However, [Joplin](https://joplinapp.org/), a markdown-based open-source note-taking app, can be a helpful tool for journaling your trades and exporting them in the required markdown format.

3. **Run the Parser**:
   - Use `markdown_parser.py` to process and import markdown files into the database.

4. **Launch the App**:
   - Start the backend API using `app.py`:
     ```bash
     python app.py
     ```
   - Then, run `dashboard.py` to launch the interactive web dashboard:
     ```bash
     python dashboard.py
     ```

## What It Can Be Used For
- Track performance across different accounts or strategies.
- Visualize key metrics like equity curves, win rates, and performance by time, day, or session.
- Gain insights into trade outcomes and strategies.
## License 📜

This project is licensed under the [GNU Affero General Public License (AGPL)](https://www.gnu.org/licenses/agpl-3.0.en.html).

### Key Features of the AGPL:

- **Freedom to Use**: You are free to use, modify, and distribute the software.
- **Copyleft Requirement**: Any modified versions of the software, as well as applications that interact with it over a network, must also be released under the AGPL.
- **Access to Source Code**: If you distribute the software or provide access to it as a service, you must make the source code available to the users.
- **Promotes Collaboration**: Encourages a collaborative development environment by requiring derived works to remain free and open.
- **No Warranty**: The software is provided "as-is" without any warranty, express or implied, including but not limited to the warranties of merchantability or fitness for a particular purpose.