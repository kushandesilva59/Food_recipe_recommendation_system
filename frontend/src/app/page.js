"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [query, setQuery] = useState("");

  const [healthy, setHealthy] = useState(false);

  const [results, setResults] = useState([]);

  const [loading, setLoading] = useState(false);

  const router = useRouter();

  async function searchRecipes() {
    if (!query) return;

    setLoading(true);

    const res = await fetch("http://127.0.0.1:5000/search", {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        query,
        healthy,
      }),
    });

    const data = await res.json();

    setResults(data.results);

    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}

      <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-4">
            🍳 Smart Leftover Recommendation
          </h1>

          <p className="text-lg opacity-90">
            Find the best recipes using your ingredients
          </p>

          {/* Search Box */}

          <div className="mt-6 flex justify-center">
            <input
              type="text"
              placeholder="Enter ingredients (chicken, rice, egg)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-96 px-4 py-3 rounded-l-lg text-black outline"
            />

            <button
              onClick={searchRecipes}
              className="bg-black px-6 py-3 rounded-r-lg hover:bg-gray-800 cursor-pointer"
            >
              Search
            </button>
          </div>

          {/* Healthy Toggle */}

          <div className="mt-4">
            <label className="flex items-center justify-center gap-2">
              <input
                type="checkbox"
                checked={healthy}
                onChange={() => setHealthy(!healthy)}
                className="cursor-pointer"
              />
              Healthy Recipes Only
            </label>
          </div>
        </div>
      </div>

      {/* Results */}

      <div className="max-w-5xl mx-auto p-6">
        {loading && (
          <p className="text-center text-gray-500">Searching recipes...</p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.map((recipe) => (
            <div
              key={recipe.id}
              onClick={() => router.push(`/recipe/${recipe.id}`)}
              className="bg-white rounded-xl shadow-md hover:shadow-xl cursor-pointer transition p-5"
            >
              <h2 className="font-bold text-lg mb-2">{recipe.name}</h2>

              <div className="text-sm text-gray-500 space-y-1">
                <p>🔥 {recipe.calories} calories</p>

                <p>⏱ {recipe.minutes} minutes</p>

                <p>🥗 {recipe.n_ingredients} ingredients</p>
              </div>

              <div className="mt-3">
                <span className="text-green-600 font-medium">
                  View Recipe →
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
