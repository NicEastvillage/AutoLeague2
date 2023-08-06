
const blueTeamName = document.getElementById("team-name-blue");
const blueDevName = document.getElementById("dev-name-blue");
const orangeTeamName = document.getElementById("team-name-orange");
const orangeDevName = document.getElementById("dev-name-orange");
const blueWinContainer = document.getElementById("blue-wins");
const orangeWinContainer = document.getElementById("orange-wins");
const winTemplateElement = document.createElement("img");
winTemplateElement.classList.add("win-indicator");
let previousData;
let tipCards;
function pollMatchInfo() {
	try {
		$.get("current_match.json", function (data) {
			if (data != previousData) {
				previousData = data;
				const info = JSON.parse(data);
				blueTeamName.innerText = info.blue[0].name;
				orangeTeamName.innerText = info.orange[0].name;

				blueDevName.innerText = info.blue[0].developer ?? "";
				orangeDevName.innerText = info.orange[0].developer ?? "";
				blueDevName.innerText += info.blue[0].language ? ` - ${info.blue[0].language.toLowerCase()}` : "";
				orangeDevName.innerText += info.orange[0].language ? ` - ${info.orange[0].language.toLowerCase()}` : "";

				blueWinContainer.innerHTML = "";
				orangeWinContainer.innerHTML = "";

				tipCards = [];
				for (let bots of [info.blue, info.orange])
					for (let bot of bots) {
						// tipCards.push({
						// 	title: `${bot.name.trim()}`,
						// 	text: `Developed by: ${bot.developer.trim()}\nLanguage: ${bot.language.trim()}`
						// });
						if (bot.description.trim().length)
							tipCards.push({
								title: `${bot.name.trim()}`,
								text: bot.description.trim(),
							});
						if (bot.fun_fact.trim().length)
							tipCards.push({
								title: `Fun fact about ${bot.name.trim()}`,
								text: bot.fun_fact.trim(),
							});
					}
			}
		}, "text");
	} catch (ex) {
		console.error(ex);
	}
	setTimeout(pollMatchInfo, 1000);
}
pollMatchInfo();


const tipCardEl = document.getElementById("tipcard");
const tipTitleEl = tipCardEl.querySelector("div[tip-title]");
const tipTextEl = tipCardEl.querySelector("div[tip-text]");
setInterval(function () {
	if (!tipCards || tipCards.length == 0)
		return;
	const tipCard = tipCards[Math.floor(Math.random() * tipCards.length)];
	tipTitleEl.innerText = tipCard.title;
	tipTextEl.innerText = tipCard.text;
	tipCardEl.setAttribute("visible", "");
	setTimeout(_ => tipCardEl.removeAttribute("visible"), 10*1000);
}, 65*1000);