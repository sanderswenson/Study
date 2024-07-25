const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const { breakdownGoal } = require('./goalBreakdown');

const app = express();
const port = process.env.PORT || 3000;

app.use(bodyParser.json());
app.use(express.static('public'));

app.post('/api/breakdown', async (req, res) => {
    console.log('Received request body:', req.body);
    const { goal } = req.body;
    console.log('Received goal:', goal);  // Debug log
    try {
        const tasks = await breakdownGoal(goal);
        console.log('Returning tasks:', tasks);  // Debug log
        res.json(tasks);
    } catch (error) {
        console.error('Error in /api/breakdown:', error);
        res.status(500).json({ error: 'An error occurred while processing the goal', details: error.message });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});