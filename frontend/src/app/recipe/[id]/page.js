"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function RecipeDetail() {
  const { id } = useParams();
  const router = useRouter();

  const [recipe, setRecipe] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(""); // ✅ For toast message

  useEffect(() => {
    fetch(`http://127.0.0.1:5000/recipe/${id}`)
      .then((res) => res.json())
      .then((data) => setRecipe(data.recipe));
  }, [id]);

  async function sendFeedback(value) {
    setFeedback(value);
    setLoading(true);

    await fetch("http://127.0.0.1:5000/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipe_id: id,
        query: "",
        helpful: value,
      }),
    });

    setLoading(false);

    // ✅ Show toast
    setToast("✅ Thank you for your feedback!");

    // ✅ Redirect after 1.5 seconds
    setTimeout(() => {
      router.push("/");
    }, 1500);
  }

  if (!recipe) {
    return <div className="p-10 text-center">Loading recipe...</div>;
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="bg-white shadow-lg rounded-xl p-6">
        <h1 className="text-3xl font-bold mb-2">{recipe.name}</h1>
        <p className="text-gray-500 mb-4">🔥 {recipe.calories} calories</p>

        <h2 className="font-semibold mb-2">Ingredients</h2>
        <ul className="list-disc ml-5 mb-5">
          {recipe.ingredients_list.map((i, index) => (
            <li key={index}>{i}</li>
          ))}
        </ul>

        <h2 className="font-semibold mb-2">Steps</h2>
        <ul className="list-decimal ml-5 mb-6">
          {recipe.steps_list.map((s, index) => (
            <li key={index}>{s}</li>
          ))}
        </ul>

        {/* Feedback Section */}
        <div className="border-t pt-4">
          <p className="font-medium mb-3">Was this recommendation helpful?</p>

          <div className="flex gap-4">
            <button
              onClick={() => sendFeedback(1)}
              className={`px-5 py-2 rounded-lg border transition
                ${
                  feedback === 1
                    ? "bg-green-500 text-white border-green-500"
                    : "bg-white hover:bg-green-50 border-gray-300"
                }`}
            >
              👍 Helpful
            </button>

            <button
              onClick={() => sendFeedback(0)}
              className={`px-5 py-2 rounded-lg border transition
                ${
                  feedback === 0
                    ? "bg-red-500 text-white border-red-500"
                    : "bg-white hover:bg-red-50 border-gray-300"
                }`}
            >
              👎 Not Helpful
            </button>
          </div>

          {loading && <p className="text-gray-500 mt-3">Saving feedback...</p>}

          {/* ✅ Toast Message */}
          {toast && (
            <div className="fixed top-5 right-5 bg-green-500 text-white px-4 py-2 rounded shadow-lg transition-all">
              {toast}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
