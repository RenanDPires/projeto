export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const response = await env.ASSETS.fetch(request);
    if (response.status !== 404) {
      return response;
    }

    const fallbackUrl = new URL("/index.html", url);
    return env.ASSETS.fetch(new Request(fallbackUrl, request));
  },
};