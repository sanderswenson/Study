const axios = require('axios');
const OpenAI = require('openai');
require('dotenv').config();

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

class Task {
    constructor(name) {
        this.name = name;
        this.subTasks = [];
    }
}

class GoalExpander {
    constructor(aiProvider, config) {
        this.aiProvider = aiProvider;
        this.config = config;
    }

    async expandGoal(goalName) {
        console.log('Expanding goal:', goalName);  // Debug log
        const prompt = this.config.promptTemplate
            .replace('{goal}', goalName)
            .replace('{num_tasks}', this.config.numTasks);
        console.log('Generated prompt:', prompt);  // Debug log

        const response = await this.aiProvider.generateText(prompt);
        console.log('AI response:', response);  // Debug log

        const tasks = response.split('\n').map(line => line.split('.').slice(1).join('.').trim()).filter(Boolean);
        console.log('Parsed tasks:', tasks);  // Debug log

        const goal = new Task(goalName);
        goal.subTasks = tasks.map(task => new Task(task));
        console.log('Created goal object:', JSON.stringify(goal, null, 2));  // Debug log

        return goal;
    }
}

const aiProvider = {
    async generateText(prompt) {
        try {
            console.log('Calling OpenAI API with prompt:', prompt);  // Debug log
            const response = await openai.chat.completions.create({
                model: "gpt-3.5-turbo",
                messages: [
                    { role: "system", content: "You are a professional project manager with expertise in task breakdown." },
                    { role: "user", content: prompt }
                ],
                max_tokens: 250,
                temperature: 0.7
            });
            console.log('OpenAI API response:', JSON.stringify(response, null, 2));  // Debug log
            return response.choices[0].message.content.trim();
        } catch (error) {
            console.error('Error calling OpenAI:', error);
            throw error;
        }
    }
};

const config = {
    numTasks: 10,
    promptTemplate: 'Break down this task "{goal}" into {num_tasks} sub-tasks. Consider:\n1. Each sub-task should be clear, concise, and directly related to the main task.\n2. Cover all necessary aspects to complete the main task.\n3. Organize sub-tasks in a logical sequence or priority order.\n4. Ensure sub-tasks specific enough for further intrumental goals.\nProvide your response as a numbered list:\n1. [First sub-task]\n2. [Second sub-task]\n3. [Third sub-task]\n...\nOnly list the sub-tasks without additional explanations.'
};

const goalExpander = new GoalExpander(aiProvider, config);

async function breakdownGoal(goal) {
    try {
        console.log('Breaking down goal:', goal);  // Debug log
        const expandedGoal = await goalExpander.expandGoal(goal);
        console.log('Expanded goal:', JSON.stringify(expandedGoal, null, 2));  // Debug log
        const tasks = expandedGoal.subTasks.map(task => task.name);
        console.log('Final tasks array:', tasks);  // Debug log
        return tasks;
    } catch (error) {
        console.error('Error in breakdownGoal:', error);
        throw error;
    }
}

module.exports = { breakdownGoal };