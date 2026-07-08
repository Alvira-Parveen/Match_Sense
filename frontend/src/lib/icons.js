import React from "react";
import { Star as PStar, StarFour } from "@phosphor-icons/react";

// Thin wrappers so components have consistent star icons w/ filled + outline variants.
export const Star = (props) => <PStar {...props} />;
export const StarBold = (props) => <PStar {...props} weight="fill" />;
export const Sparkle = (props) => <StarFour {...props} weight="fill" />;
