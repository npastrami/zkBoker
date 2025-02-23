const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');

module.exports = {
    entry: {
        editor: './staticfiles/js/editor.jsx'
    },
    output: {
        path: path.resolve(__dirname, 'staticfiles', 'js', 'dist'),
        filename: '[name].bundle.js',
        publicPath: '/static/js/dist/'
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env', '@babel/preset-react']
                    }
                }
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            }
        ]
    },
    resolve: {
        extensions: ['.js', '.jsx'],
        modules: [
            path.resolve(__dirname, 'staticfiles/js'),
            'node_modules'
        ]
    },
    plugins: [
        new BundleTracker({
            path: __dirname,
            filename: 'webpack-stats.json'
        })
    ],
    devtool: 'source-map'
};