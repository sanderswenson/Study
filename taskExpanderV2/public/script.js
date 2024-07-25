document.getElementById('goalForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const mainGoal = document.getElementById('mainGoal').value;
    console.log('Submitting goal:', mainGoal);  // Debug log
    try {
        const response = await fetch('/api/breakdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ goal: mainGoal }),
        });
        console.log('Response status:', response.status);  // Debug log
        const tasks = await response.json();
        console.log('Received tasks:', tasks);  // Debug log
        displayTasks(mainGoal, tasks);
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing your request.');
    }
});

function displayTasks(mainGoal, tasks) {
    console.log('Displaying tasks for goal:', mainGoal);
    console.log('Tasks to display:', tasks);
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '';
    
    // Display the main goal
    const mainGoalElement = document.createElement('div');
    mainGoalElement.className = 'main-goal';
    mainGoalElement.innerHTML = `<h2>Main Goal: ${mainGoal}</h2>`;
    taskList.appendChild(mainGoalElement);

    // Display subtasks
    if (!Array.isArray(tasks) || tasks.length === 0) {
        taskList.innerHTML += '<p>No tasks were generated. Please try again.</p>';
        return;
    }

    tasks.forEach((task, index) => {
        const taskElement = document.createElement('div');
        taskElement.className = 'task';
        const taskName = typeof task === 'string' ? task : JSON.stringify(task);
        taskElement.innerHTML = `
            <p>${index + 1}. ${taskName}</p>
            <button onclick="breakdownTask(${index}, '${taskName.replace(/'/g, "\\'")}')">Break Down Further</button>
            <div class="subtasks" id="subtasks-${index}"></div>
        `;
        taskList.appendChild(taskElement);
    });
    console.log('Tasks displayed');
}

async function breakdownTask(index, task) {
    console.log('Breaking down task:', task, 'at index:', index);
    try {
        const response = await fetch('/api/breakdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ goal: task }),
        });
        console.log('Subtask response status:', response.status);
        const subtasks = await response.json();
        console.log('Received subtasks:', subtasks);
        const subtaskList = document.getElementById(`subtasks-${index}`);
        subtaskList.innerHTML = subtasks.map((subtask, i) => {
            return `
                <div class="task">
                    <p>${i + 1}. ${subtask}</p>
                    <button onclick="breakdownTask('${index}-${i}', '${subtask.replace(/'/g, "\\'")}')">Break Down Further</button>
                    <div class="subtasks" id="subtasks-${index}-${i}"></div>
                </div>
            `;
        }).join('');
        console.log('Subtasks displayed');
    } catch (error) {
        console.error('Error in breakdownTask:', error);
        alert('An error occurred while breaking down the task.');
    }
}