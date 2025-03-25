import typescriptEslint from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
// Add imports for eslint-config-prettier
import eslintConfigPrettier from "eslint-config-prettier";

export default [
    {
        files: ["**/*.ts"]
    },
    {
        plugins: {
            "@typescript-eslint": typescriptEslint
        },

        languageOptions: {
            parser: tsParser,
            ecmaVersion: 2022,
            sourceType: "module"
        },

        rules: {
            "@typescript-eslint/naming-convention": [
                "warn",
                {
                    selector: "import",
                    format: ["camelCase", "PascalCase"]
                }
            ],

            curly: "warn",
            eqeqeq: "warn",
            "no-throw-literal": "warn",
            semi: "warn"
        }
    },
    // Add prettier config to avoid conflicts
    eslintConfigPrettier
];
