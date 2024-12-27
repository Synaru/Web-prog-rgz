function yearChange() {
    let inputElement = document.getElementById('yearInput')
    console.log(inputElement.value)
    loadWeeks()
}

async function logout() {
    let res = await fetch('/logout')
    if(!res.ok){ return }
    window.location.reload();
}

async function onWeekClick(week, user_id, element) {
    if(element.classList.contains('locked')){
        return
    }
    let inputElement = document.getElementById('yearInput')
    //validate 4 weeks total
    if(!user_id){
        let res = await fetch('/selectweek', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "week": week,
            "year": inputElement.value
        })
        })

        if(res.ok){
            loadWeeks()
        }
    } else {
        let res = await fetch('/deselectweek', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "week": week
        })
        })

        if(res.ok){
            loadWeeks()
        }
    }
}

async function loadWeeks() {
    let inputElement = document.getElementById('yearInput')
    let weeksRes = await fetch(`/weekslist?year=${inputElement.value}`)
    if(!weeksRes.ok){return}
    let weeks = await weeksRes.json()

    for (let i = 0; i < 12; i++) {
        let relatedWeeks = []

        for(let week of weeks){
            if(new Date(week.start).getMonth() === i){
                relatedWeeks.push(week)
            }
        }
        let html = ``
        for(let week of relatedWeeks){
            let start = new Date(week.start)
            let end = new Date(week.end)
            let name = week.name
            let startDisplay = `${padNumberWithZeroes(start.getDate(),2)}.${padNumberWithZeroes(start.getMonth() + 1,2)}`
            let endDisplay = `${padNumberWithZeroes(end.getDate(),2)}.${padNumberWithZeroes(end.getMonth() + 1,2)}`
            let locked = start < new Date()

            html += `
                <div class="week-widget ${name ?? 'free'} ${locked ? 'locked' : ''}" onclick="onWeekClick(${week.id}, ${week.user_id}, this)">
                    ${startDisplay}-${endDisplay} ${name ?? ''}
                </div>
            `
        }

        let relatedWeekContainer = document.getElementById(`${i}_weeks`)
        relatedWeekContainer.innerHTML = html
    }
}

function padNumberWithZeroes(num, length) {
    let str = Math.abs(num).toString();
    while (str.length < length) {
        str = '0' + str;
    }
    return num >= 0 ? str : '-' + str.slice(1);
}

