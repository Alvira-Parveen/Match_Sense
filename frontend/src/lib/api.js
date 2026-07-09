import axios from "axios";

const BASE = process.env.REACT_APP_BACKEND_URL || "https://match-sense-backend.onrender.com";
export const API = `${BASE}/api`;

export const api = axios.create({ baseURL: API, timeout: 60000 });

export const getTeams = () => api.get("/teams").then((r) => r.data);
export const getBracket = () => api.get("/bracket").then((r) => r.data);
export const getPrediction = (mid) =>
    api.get(`/predict/${mid}`).then((r) => r.data);
export const getSimulation = (runs = 10000) =>
    api.get(`/simulate?runs=${runs}`).then((r) => r.data);
export const getMatchBrief = (mid) =>
    api.get(`/match-brief/${mid}`).then((r) => r.data);
export const getAudioSummary = (mid, voice = "nova", lang = "en") =>
    api.get(`/audio-summary/${mid}?voice=${voice}&lang=${lang}`).then((r) => r.data);
export const getTeamDetail = (code) =>
    api.get(`/team/${code}`).then((r) => r.data);
export const getAgentLogs = () => api.get("/agent-logs").then((r) => r.data);
export const setFavorite = (session_id, team_code) =>
    api.post("/favorites", { session_id, team_code }).then((r) => r.data);
export const getFavorite = (session_id) =>
    api.get(`/favorites/${session_id}`).then((r) => r.data);

export function flagEmoji(cc) {
    if (!cc || cc.length !== 2) return "";
    return String.fromCodePoint(
        ...[...cc.toUpperCase()].map((c) => 0x1f1e6 + c.charCodeAt(0) - 65),
    );
}
