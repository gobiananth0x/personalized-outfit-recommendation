import { useEffect, useState } from "react";
import "./OutfitSection.css";
import toast from "react-hot-toast";
import { FadeLoader } from "react-spinners";

const OutfitSection = () => {
  const [outfits, setOutfits] = useState([]);
  const [generating, setGenerating] = useState(false);

  const buildWeek = () => {
    const today = new Date();
    const week = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      const iso = d.toISOString().split("T")[0];
      week.push({
        date: iso,
        top: null,
        bottom: null,
      });
    }
    return week;
  };

  useEffect(() => {
    fetch(`${import.meta.env.VITE_BACKEND_URL}/outfits/week`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then((data) => {
        const week = buildWeek();
        const merged = week.map((day) => {
          const found = data.find((o) => o.date === day.date);
          return found ? found : day;
        });
        setOutfits(merged);
      })
      .catch(() => toast.error("Couldn't load outfits."));
  }, []);

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    const day = d.getDate().toString().padStart(2, "0");
    const month = d.toLocaleString("en-US", { month: "short" }).toUpperCase();
    const year = d.getFullYear();
    const weekday = d
      .toLocaleString("en-US", { weekday: "short" })
      .toUpperCase();
    return `${day}-${month}-${year}-${weekday}`;
  };

  const hasExistingOutfits = outfits.some((o) => o.top?.id && o.bottom?.id);
  const isPastWeek =
    outfits.length > 0 &&
    outfits[0].date < new Date().toISOString().split("T")[0];
  const buttonLabel =
    hasExistingOutfits && !isPastWeek ? "Regenerate" : "Generate";

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      const previousPlanData = outfits
        .filter((o) => o.top && o.bottom)
        .map((o) => ({
          date: o.date,
          top: o.top,
          bottom: o.bottom,
        }));
      setOutfits(buildWeek());
      const res = await fetch(
        `${import.meta.env.VITE_BACKEND_URL}/outfits/generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
          body: JSON.stringify({
            city: "",
            previous_plan: { plan: previousPlanData },
          }),
        },
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      const week = buildWeek();
      const merged = week.map((day) => {
        const found = data.find((o) => o.date === day.date);
        return found ? found : day;
      });
      setOutfits(merged);
      toast.success("Outfits generated.");
    } catch {
      toast.error("Couldn't generate outfits.");
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!allDaysReady) return;
    const payload = outfits.map((o) => ({
      date: o.date,
      top_id: o.top.id,
      bottom_id: o.bottom.id,
    }));
    try {
      const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/outfits/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error();
      toast.success("Outfits saved.");
    } catch {
      toast.error("Couldn't save.");
    }
  };

  const allDaysReady =
    outfits.length === 7 && outfits.every((o) => o.top?.id && o.bottom?.id);

  return (
    <section className="outfit-section">
      <div className="outfit-scroll">
        {outfits.map((outfit) => (
          <div className="outfit-card" key={outfit.date}>
            <div className="outfit-card-header">{formatDate(outfit.date)}</div>
            <div className="outfit-card-body">
              {generating ? (
                <div className="outfit-loader">
                  <FadeLoader height={8} width={3} radius={6} margin={2} />
                  <span>Generating...</span>
                </div>
              ) : (
                <>
                  <img
                    src={
                      outfit.top?.image_url
                        ? `${import.meta.env.VITE_BACKEND_URL}/static/uploads/${outfit.top?.image_url}`
                        : "/images/top-fallback.png"
                    }
                    alt="Top"
                  />
                  <img
                    src={
                      outfit.bottom?.image_url
                        ? `${import.meta.env.VITE_BACKEND_URL}/static/uploads/${outfit.bottom?.image_url}`
                        : "/images/bottom-fallback.png"
                    }
                    alt="Bottom"
                  />
                </>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="outfit-actions">
        <button
          className={`outfit-action-btn generate ${buttonLabel.toLowerCase()}`}
          onClick={handleGenerate}
          disabled={generating}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {buttonLabel === "Regenerate" ? (
              <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
            ) : (
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            )}
          </svg>
          {buttonLabel}
        </button>
        <button
          className="outfit-action-btn save"
          onClick={handleSave}
          disabled={!allDaysReady}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
            <polyline points="17 21 17 13 7 13 7 21" />
            <polyline points="7 3 7 8 15 8" />
          </svg>
          Save
        </button>
      </div>
    </section>
  );
};

export default OutfitSection;
