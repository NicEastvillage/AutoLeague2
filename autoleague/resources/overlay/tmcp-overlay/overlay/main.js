const POLL_INTERVAL = 200;
const JSON_PATH = 'data.json';
const ICONS = {
    "BALL": "⚽",
    "BOOST": "⛽",
    "DEMO": "💣",
    "READY": "✔️",
    "DEFEND": "🛡️",
}


const app = new Vue({
    el: '#app',
    data: {
        info: {}
    },
    methods: {
        async loadData() {
            try {
                const res = await $.get("data.json");
                this.info = JSON.parse(res);
            } catch (err) {
                console.error(err);
                this.info = {
                    actions: {},
                    active: false,
                    names: [],
                };
            }
        },
        format(value, precision=10) {
            return Math.round(value * precision) / precision;
        },
        icon(action_type) {
            return ICONS[action_type];
        },
        playerName(index) {
            return this.info.names[index];
        },
    },
    created: function() {
        this.loadData();
        setInterval(this.loadData, POLL_INTERVAL);
    }
});