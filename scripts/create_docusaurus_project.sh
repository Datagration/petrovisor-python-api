#!/bin/bash

# Setup Docusaurus in the website directory
yarn create docusaurus website classic --typescript

# Navigate to the website directory
cd website

# Install dependencies
yarn install
