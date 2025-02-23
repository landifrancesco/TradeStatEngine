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

1. **Launch the App**:
   - Start the backend API and Dashboard by running:
     ```bash
     python launcher.py
     ```
   - The interactive web dashboard will be available at: [http://127.0.0.1:8050/](http://127.0.0.1:8050/).
   - **Note**: If no database file is detected, the initialization script will automatically run to set up the database.

2. **(Optional) Modify/Add entries or accounts**:
   - If needed you can use the `database_utils.py` script located under the `utils` directory to delete or update entries in the database, add accounts, etc.

3. **Journal your trades using the template**:
   - Use the provided markdown template (`Template ✅⭕🟡⛔⬆️⬇️.md`) to format your trading journal entries.
   - You need to export the `.md` file of the trades you want to import.
   - **Important**: Ensure all required fields strictly follow the template format; otherwise, the import will fail.
   - **Note**: Although this tool isn’t inherently compatible with any specific app, I use [Joplin](https://joplinapp.org/).

4. **Import**:
   - On the main page, clicking the **Import File** button will redirect you to the upload interface.
   - (Optional) open your browser and visit: [http://127.0.0.1:5050/upload](http://127.0.0.1:5050/upload).
   - Use the provided interface to select an account from the dropdown and upload your markdown file(s). The web importer will parse your entries and import them into the database.

5. **(Optional) Use the Markdown Parser Directly**:
   - If you prefer not to rely on the web importer interface, you can use the `markdown_parser.py` script located under the `utils` directory to parse and import your markdown files directly.

## 🐳 Docker Deployment 

### **Run with Docker (Pull from GHCR)**
```bash
docker pull ghcr.io/landifrancesco/tradestatengine:latest
docker run -d -p 5000:5000 -p 5050:5050 -p 8050:8050 --name tradestatengine -v tradestatengine_data:/app/app/data ghcr.io/landifrancesco/tradestatengine:latest
```

### **Run with Docker Compose**
```bash
docker-compose up -d
```

The interactive web dashboard will be available at: [http://127.0.0.1:8050/](http://127.0.0.1:8050/).

**Stop the application:**
```bash
docker-compose down
```

**Rebuild the container (after code changes):**
```bash
docker-compose up -d --build
```

**View logs:**
```bash
docker-compose logs -f
```

## What It Can Be Used For
- Track performance across different accounts or strategies.
- Visualize key metrics like equity curves, win rates, and performance by time, day, or session.
- Gain insights into trade outcomes and strategies.

## License 📜

This project is licensed under the [GNU Affero General Public License (AGPL)](https://www.gnu.org/licenses/agpl-3.0.en.html).
