"use client";

import { useEffect, useState } from "react";

export default function TopRecipes() {
  const [recipes, setRecipes] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/top-feedback")
      .then((res) => res.json())

      .then((data) => setRecipes(data.recipes));
  }, []);

  return (
    <div className="p-10">
      <h1 className="text-3xl font-bold mb-5">Top Rated Recipes</h1>

      {recipes.map((recipe) => (
        <div key={recipe.id} className="border p-3 mb-2">
          <h2 className="font-bold">{recipe.name}</h2>

          <p>Calories: {recipe.calories}</p>

          <p>Likes: {recipe.feedback_count}</p>
        </div>
      ))}
    </div>
  );
}
