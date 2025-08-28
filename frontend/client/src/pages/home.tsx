import { Search, TrendingUp, Clock, Star, Zap, Globe, Loader2, AlertCircle, ChevronDown, User } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { 
  useLatestNews, 
  useTrending, 
  useSearchState, 
  useContentInteractions,
  useSummarization,
  useHealth
} from "../hooks/useSportsData";
import { type ContentItem } from "../lib/api";
import { AuthButton } from "@/components/auth";

export default function Home() {
  const [selectedSport, setSelectedSport] = useState<string>("");
  const [selectedArticle, setSelectedArticle] = useState<ContentItem | null>(null);
  const [showSummary, setShowSummary] = useState(false);
  
  // Pagination state
  const [allArticles, setAllArticles] = useState<ContentItem[]>([]);
  const [displayedCount, setDisplayedCount] = useState(6);
  const [nextCursor, setNextCursor] = useState<string | undefined>(undefined);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  
  // Dropdown state
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isDropdownOpen]);

  // API hooks
  const { data: healthData } = useHealth();
  const { data: latestNews, isLoading: newsLoading, error: newsError } = useLatestNews(
    selectedSport ? [selectedSport.toLowerCase()] : undefined,
    6
  );
  const { data: trendingTerms, isLoading: trendingLoading } = useTrending(5);
  const { searchRequest, updateSearch, selectContent } = useSearchState();
  const { prefetchContent, shareContent } = useContentInteractions();
  const summarizationMutation = useSummarization({
    onSuccess: () => setShowSummary(true),
  });

  // Update articles when new data arrives
  useEffect(() => {
    if (latestNews?.items) {
      setAllArticles(latestNews.items);
      setNextCursor(latestNews.next_cursor);
      setDisplayedCount(6); // Reset to show first 6
    }
  }, [latestNews]);

  // Reset pagination when sport changes
  useEffect(() => {
    setAllArticles([]);
    setDisplayedCount(6);
    setNextCursor(undefined);
  }, [selectedSport]);

  const categories = [
    { name: "NBA", icon: "🏀", sport: "basketball" },
    { name: "NFL", icon: "🏈", sport: "football" },
    { name: "MLB", icon: "⚾", sport: "baseball" },
    { name: "NHL", icon: "🏒", sport: "hockey" },
    { name: "SOCCER", icon: "⚽", sport: "soccer" },
    { name: "COLLEGE", icon: "🎓", sport: "college" },
    { name: "TENNIS", icon: "🎾", sport: "tennis" },
    { name: "GOLF", icon: "⛳", sport: "golf" },
    { name: "OLYMPICS", icon: "🏅", sport: "olympics" },
    { name: "ESPORTS", icon: "🎮", sport: "esports" }
  ];

  const inspirationTags = ["AI POWERED", "⚡ REAL-TIME", "PERSONALIZED"];

  // Handle article selection and summarization
  const handleArticleClick = async (article: ContentItem) => {
    setSelectedArticle(article);
    selectContent(article);
    
    // Generate AI summary
    summarizationMutation.mutate({
      content_ids: [article.id],
      summary_type: "brief",
      max_length: 150,
    });
  };

  // Handle sport category selection
  const handleSportSelect = (sport: string) => {
    setSelectedSport(selectedSport === sport ? "" : sport);
  };

  // Handle load more articles
  const handleLoadMore = async () => {
    if (isLoadingMore || !nextCursor) return;
    
    setIsLoadingMore(true);
    try {
      // For now, just show more from existing articles
      // In a real implementation, you'd fetch more data with the cursor
      const newDisplayCount = Math.min(displayedCount + 6, allArticles.length);
      setDisplayedCount(newDisplayCount);
      
      // If we've shown all current articles and there are more available
      if (newDisplayCount >= allArticles.length && latestNews?.has_more) {
        // Here you would typically make another API call with the cursor
        // For now, we'll just disable the button
        setNextCursor(undefined);
      }
    } finally {
      setIsLoadingMore(false);
    }
  };

  // Prefetch content on hover
  const handleArticleHover = (articleId: string) => {
    prefetchContent(articleId);
  };

  // Get display articles (show only the first displayedCount articles)
  const displayArticles = allArticles.slice(0, displayedCount);

  // System status indicator
  const isSystemHealthy = healthData?.status === 'healthy';
  const isLiveData = latestNews?.engine !== 'mock';

  // Format time ago
  const formatTimeAgo = (dateString?: string) => {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gray-bg">
      {/* Navigation Header */}
      <nav className="w-full px-4 sm:px-6 py-3 sm:py-4 bg-gray-bg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo with Dropdown */}
          <div className="flex-shrink-0 relative" ref={dropdownRef}>
            <button 
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-1 sm:gap-2 text-lg sm:text-xl font-black text-black tracking-tight hover:text-gray-700 transition-colors"
            >
              MLB
              <ChevronDown className={`w-3 h-3 sm:w-4 sm:h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {/* Dropdown Menu */}
            {isDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-40 sm:w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <div className="py-2">
                  {/* Dropdown items will be added later */}
                  <div className="px-3 sm:px-4 py-2 text-xs sm:text-sm text-gray-500">
                    Coming soon...
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Authentication Button */}
          <AuthButton variant="outline" size="sm" />
        </div>
      </nav>

      {/* Main Content Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        {/* Hero Section */}
        <section className="py-8 sm:py-12">
          {/* Trending Section */}
          {!trendingLoading && trendingTerms && trendingTerms.length > 0 && (
            <div className="mb-6 sm:mb-8">
              <div className="flex items-center gap-2 mb-3 sm:mb-4">
                <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 text-red-500" />
                <span className="text-xs sm:text-sm font-semibold text-black">TRENDING NOW</span>
              </div>
              <div className="flex flex-wrap gap-1.5 sm:gap-2">
                {trendingTerms.slice(0, 5).map((term, index) => (
                  <span
                    key={index}
                    className="px-2 sm:px-3 py-1 text-xs font-medium text-red-600 bg-red-50 border border-red-200 rounded-full hover:bg-red-100 transition-colors cursor-pointer"
                  >
                    {term.term} {term.is_trending && '🔥'}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Category Tags */}
          <div className="flex flex-wrap justify-center gap-2 sm:gap-3 mb-8 sm:mb-12">
            {categories.map((category, index) => (
              <span
                key={index}
                onClick={() => handleSportSelect(category.sport)}
                className={`px-2 sm:px-3 py-1 text-xs font-medium border rounded-full transition-colors cursor-pointer ${
                  selectedSport === category.sport
                    ? 'bg-black text-white border-black'
                    : 'text-black border-black hover:bg-black hover:text-white'
                }`}
              >
                <span className="hidden sm:inline">{category.icon} </span>{category.name}
              </span>
            ))}
          </div>
          
          {/* Live Scores Table */}
          <div className="max-w-4xl mx-auto px-4">
            <div className="bg-white/20 backdrop-blur-md rounded-xl shadow-2xl border border-white/30 overflow-hidden relative">
              {/* Glass effect overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none"></div>
              
              {/* Header */}
              <div className="bg-white/10 backdrop-blur-sm px-4 sm:px-6 py-3 border-b border-white/20 relative z-10">
                <h3 className="text-sm sm:text-base font-semibold text-gray-900 text-center">
                  Live Scores
                </h3>
              </div>
              
              {/* Scores Grid */}
              <div className="p-3 sm:p-4 space-y-3 sm:space-y-4 relative z-10">
                {/* Game 1 */}
                <div className="flex items-center justify-between bg-white/30 backdrop-blur-sm rounded-lg p-3 sm:p-4 border border-white/20 shadow-lg">
                  <div className="flex items-center space-x-2 sm:space-x-3 flex-1">
                    <div className="w-6 h-6 sm:w-8 sm:h-8 bg-blue-600/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg border border-white/20">
                      <span className="text-white text-xs sm:text-sm font-bold">LAL</span>
                    </div>
                    <span className="text-lg sm:text-xl font-bold text-gray-900 drop-shadow-sm">108</span>
                  </div>
                  
                  <div className="text-center px-2 sm:px-4">
                    <div className="text-xs sm:text-sm text-gray-700 font-medium bg-white/20 backdrop-blur-sm px-2 py-1 rounded-full border border-white/30">FINAL</div>
                  </div>
                  
                  <div className="flex items-center space-x-2 sm:space-x-3 flex-1 justify-end">
                    <span className="text-lg sm:text-xl font-bold text-gray-900 drop-shadow-sm">112</span>
                    <div className="w-6 h-6 sm:w-8 sm:h-8 bg-green-600/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg border border-white/20">
                      <span className="text-white text-xs sm:text-sm font-bold">BOS</span>
                    </div>
                  </div>
                </div>
                
                {/* Game 2 */}
                <div className="flex items-center justify-between bg-white/30 backdrop-blur-sm rounded-lg p-3 sm:p-4 border border-white/20 shadow-lg">
                  <div className="flex items-center space-x-2 sm:space-x-3 flex-1">
                    <div className="w-6 h-6 sm:w-8 sm:h-8 bg-red-600/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg border border-white/20">
                      <span className="text-white text-xs sm:text-sm font-bold">MIA</span>
                    </div>
                    <span className="text-lg sm:text-xl font-bold text-gray-900 drop-shadow-sm">95</span>
                  </div>
                  
                  <div className="text-center px-2 sm:px-4">
                    <div className="text-xs sm:text-sm text-red-600 font-medium bg-red-100/40 backdrop-blur-sm px-2 py-1 rounded-full border border-red-200/50 animate-pulse">Q3 8:42</div>
                  </div>
                  
                  <div className="flex items-center space-x-2 sm:space-x-3 flex-1 justify-end">
                    <span className="text-lg sm:text-xl font-bold text-gray-900 drop-shadow-sm">89</span>
                    <div className="w-6 h-6 sm:w-8 sm:h-8 bg-yellow-500/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg border border-white/20">
                      <span className="text-white text-xs sm:text-sm font-bold">GSW</span>
                    </div>
                  </div>
                </div>
                
                {/* Game 3 */}
                <div className="flex items-center justify-between bg-white/30 backdrop-blur-sm rounded-lg p-3 sm:p-4 border border-white/20 shadow-lg">
                  <div className="flex items-center space-x-2 sm:space-x-3 flex-1">
                    <div className="w-6 h-6 sm:w-8 sm:h-8 bg-purple-600/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg border border-white/20">
                      <span className="text-white text-xs sm:text-sm font-bold">NYK</span>
                    </div>
                    <span className="text-lg sm:text-xl font-bold text-gray-600 drop-shadow-sm">--</span>
                  </div>
                  
                  <div className="text-center px-2 sm:px-4">
                    <div className="text-xs sm:text-sm text-gray-700 font-medium bg-blue-100/40 backdrop-blur-sm px-2 py-1 rounded-full border border-blue-200/50">8:00 PM</div>
                  </div>
                  
                  <div className="flex items-center space-x-2 sm:space-x-3 flex-1 justify-end">
                    <span className="text-lg sm:text-xl font-bold text-gray-600 drop-shadow-sm">--</span>
                    <div className="w-6 h-6 sm:w-8 sm:h-8 bg-orange-600/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg border border-white/20">
                      <span className="text-white text-xs sm:text-sm font-bold">PHX</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Inspiration Quote Section */}
      <section className="bg-dark-section py-12 sm:py-16 mb-12 sm:mb-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 sm:gap-12 lg:gap-16 items-center">
            {/* Quote Content */}
            <div className="space-y-6 sm:space-y-8 text-center lg:text-left">
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-light text-white font-serif leading-tight">
                Smart sports news that adapts to your passions.
              </h2>
              
              <p className="text-white opacity-90 text-sm sm:text-base leading-relaxed max-w-lg mx-auto lg:mx-0">
                AI-powered curation finds the most relevant sports content from trusted sources, intelligently summarized and ranked by your favorite teams and interests.
              </p>
              
              {/* Tags */}
              <div className="flex flex-wrap justify-center lg:justify-start gap-2 sm:gap-3">
                {inspirationTags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 sm:px-3 py-1 text-xs font-medium text-white border border-white rounded-full hover:bg-white hover:text-black transition-colors cursor-pointer"
                  >
                    {tag}
                  </span>
                ))}
                <span className="w-7 h-7 sm:w-8 sm:h-8 bg-white rounded-full flex items-center justify-center hover:bg-gray-200 transition-colors cursor-pointer">
                  <svg className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </div>
            
            {/* Image */}
            <div className="flex justify-center lg:justify-end order-first lg:order-last">
              <img 
                src="https://images.unsplash.com/photo-1578662996442-48f60103fc96?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=800&h=1000"
                alt="Sports analytics dashboard"
                className="w-48 h-60 sm:w-56 sm:h-72 lg:w-64 lg:h-80 object-cover object-center rounded-lg"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Article Preview Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pb-12 sm:pb-16">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 sm:mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-black">
            {selectedSport ? `${selectedSport.toUpperCase()} News` : 'Latest Sports News'}
          </h2>
          
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
            {newsLoading && (
              <div className="flex items-center gap-2 text-gray-600">
                <Loader2 className="w-3 h-3 sm:w-4 sm:h-4 animate-spin" />
                <span className="text-xs sm:text-sm">Loading...</span>
              </div>
            )}
            

          </div>
        </div>

        {/* Error State */}
        {newsError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 sm:p-4 mb-6 sm:mb-8">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-3 h-3 sm:w-4 sm:h-4 text-red-600" />
              <span className="text-xs sm:text-sm font-medium text-red-800">
                Unable to load latest news. Showing cached content.
              </span>
            </div>
          </div>
        )}

        {/* Articles Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          {displayArticles.map((article) => (
            <article 
              key={article.id} 
              className="group cursor-pointer bg-white rounded-lg shadow-sm hover:shadow-md transition-all duration-200"
              onClick={() => handleArticleClick(article)}
              onMouseEnter={() => handleArticleHover(article.id)}
            >
              <div className="relative">
                <img 
                  src={article.image_url || "https://images.unsplash.com/photo-1546519638-68e109498ffc?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&h=600"}
                  alt={article.title}
                  className="w-full h-40 sm:h-48 object-cover rounded-t-lg group-hover:opacity-90 transition-opacity"
                />
                
                {/* Quality Score Badge */}
                <div className="absolute top-2 right-2 bg-black bg-opacity-75 text-white text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full">
                  {Math.round(article.quality_score * 100)}%
                </div>
                
                {/* Time Badge */}
                {article.published_at && (
                  <div className="absolute bottom-2 left-2 bg-white bg-opacity-90 text-black text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full flex items-center gap-1">
                    <Clock className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                    <span className="hidden sm:inline">{formatTimeAgo(article.published_at)}</span>
                  </div>
                )}
              </div>
              
              <div className="p-3 sm:p-4">
                <div className="flex items-center gap-1.5 sm:gap-2 mb-2">
                  <span className="text-xs font-medium text-gray-600 truncate">{article.source_name}</span>
                  {article.sports_keywords.length > 0 && (
                    <span className="text-xs text-blue-600 bg-blue-50 px-1.5 sm:px-2 py-0.5 rounded flex-shrink-0">
                      {article.sports_keywords[0]}
                    </span>
                  )}
                </div>
                
                <h3 className="text-sm sm:text-lg font-semibold text-black mb-2 group-hover:text-gray-700 transition-colors line-clamp-2">
                  {article.title}
                </h3>
                
                {article.summary && (
                  <p className="text-gray-600 text-xs sm:text-sm line-clamp-2 mb-2 sm:mb-3">
                    {article.summary}
                  </p>
                )}
                
                {article.byline && (
                  <p className="text-xs text-gray-500 truncate">
                    {article.byline}
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>

        {/* Load More Button */}
        {(displayedCount < allArticles.length || (latestNews?.has_more && nextCursor)) && (
          <div className="text-center mt-6 sm:mt-8">
            <button 
              onClick={handleLoadMore}
              disabled={isLoadingMore}
              className="px-4 sm:px-6 py-2.5 sm:py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors font-medium text-sm sm:text-base w-full sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mx-auto"
            >
              {isLoadingMore ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading...
                </>
              ) : (
                `Load More Articles (${Math.min(6, allArticles.length - displayedCount)} more)`
              )}
            </button>
          </div>
        )}
      </section>

      {/* AI Summary Modal */}
      {selectedArticle && showSummary && summarizationMutation.data && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-3 sm:p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[85vh] sm:max-h-[80vh] overflow-y-auto">
            <div className="p-4 sm:p-6">
              <div className="flex items-start justify-between mb-3 sm:mb-4">
                <h3 className="text-lg sm:text-xl font-bold text-black pr-4">
                  AI Summary
                </h3>
                <button 
                  onClick={() => setShowSummary(false)}
                  className="text-gray-500 hover:text-black text-lg sm:text-xl p-1"
                >
                  ✕
                </button>
              </div>
              
              <div className="mb-3 sm:mb-4">
                <h4 className="font-semibold text-gray-900 mb-2 text-sm sm:text-base">{selectedArticle.title}</h4>
                <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-600 mb-3 sm:mb-4">
                  <span>{selectedArticle.source_name}</span>
                  <span className="hidden sm:inline">•</span>
                  <span>{formatTimeAgo(selectedArticle.published_at)}</span>
                  <span className="hidden sm:inline">•</span>
                  <span>Quality: {Math.round(selectedArticle.quality_score * 100)}%</span>
                </div>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-3 sm:p-4 mb-3 sm:mb-4">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <Zap className="w-3 h-3 sm:w-4 sm:h-4 text-blue-600" />
                  <span className="text-xs sm:text-sm font-medium text-gray-900">AI-Generated Summary</span>
                  <span className="text-xs text-gray-600">
                    Confidence: {Math.round(summarizationMutation.data.confidence_score * 100)}%
                  </span>
                </div>
                <p className="text-gray-800 leading-relaxed text-sm sm:text-base">
                  {summarizationMutation.data.summary}
                </p>
              </div>
              
              {summarizationMutation.data.key_entities && summarizationMutation.data.key_entities.length > 0 && (
                <div className="mb-3 sm:mb-4">
                  <h5 className="text-xs sm:text-sm font-medium text-gray-900 mb-2">Key Entities</h5>
                  <div className="flex flex-wrap gap-1.5 sm:gap-2">
                    {summarizationMutation.data.key_entities.map((entity, index) => (
                      <span key={index} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 sm:pt-4 border-t">
                <div className="text-xs text-gray-500 text-center sm:text-left">
                  Generated in {Math.round(summarizationMutation.data.generation_time_ms)}ms
                </div>
                <div className="flex flex-col sm:flex-row gap-2">
                  <button 
                    onClick={() => shareContent(selectedArticle)}
                    className="px-3 sm:px-4 py-2 text-xs sm:text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                  >
                    Share
                  </button>
                  <a 
                    href={selectedArticle.canonical_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 sm:px-4 py-2 text-xs sm:text-sm bg-black text-white rounded hover:bg-gray-800 transition-colors text-center"
                  >
                    Read Full Article
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading overlay for summarization */}
      {summarizationMutation.isPending && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-4 sm:p-6 flex items-center gap-3 mx-4">
            <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin text-blue-600" />
            <span className="text-gray-900 text-sm sm:text-base">Generating AI summary...</span>
          </div>
        </div>
      )}
    </div>
  );
}

